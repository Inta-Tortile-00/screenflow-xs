import os
import random
import time
from pathlib import Path
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.utils import platform
from xs_controller import ModuleController
from android_bridge import AndroidBridge
from queue_engine import ShuffleQueue, IntervalClock

EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}

class Notifier:
    def __init__(self):
        self.enabled = False
        if platform != 'android':
            return
        try:
            from jnius import autoclass
            self.autoclass = autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            self.context = PythonActivity.mActivity
            self.manager = self.context.getSystemService('notification')
            self.NotificationBuilder = autoclass('android.app.Notification$Builder')
            self.NotificationChannel = autoclass('android.app.NotificationChannel')
            self.VERSION = autoclass('android.os.Build$VERSION')
            self.channel_id = 'screenflow_status'
            if self.VERSION.SDK_INT >= 26:
                channel = self.NotificationChannel(self.channel_id, 'ScreenFlow slideshow', 2)
                self.manager.createNotificationChannel(channel)
            self.enabled = True
        except Exception as exc:
            print('Notification initialization failed:', exc)

    def update(self, title, detail):
        if not self.enabled:
            return
        try:
            if self.VERSION.SDK_INT >= 26:
                builder = self.NotificationBuilder(self.context, self.channel_id)
            else:
                builder = self.NotificationBuilder(self.context)
            icon = self.context.getApplicationInfo().icon
            builder.setSmallIcon(icon)
            builder.setContentTitle(title)
            builder.setContentText(detail)
            builder.setOngoing(True)
            builder.setOnlyAlertOnce(True)
            self.manager.notify(4821, builder.build())
        except Exception as exc:
            print('Notification update failed:', exc)

    def clear(self):
        if self.enabled:
            self.manager.cancel(4821)

class ScreenFlow(App):
    def build(self):
        self.title = 'ScreenFlow XS Wrapper'
        self.module_controller = ModuleController()
        self.bridge = AndroidBridge()
        self.xs_queue = ShuffleQueue()
        self.xs_clock = IntervalClock()
        self.xs_entries = {}
        self.xs_mode = "wallpaper"
        self.module_running = False
        self.module_deadline = None
        self.module_started = None
        self.files = []
        self.queue = []
        self.current = None
        self.index = 0
        self.transitions = 0
        self.started_at = None
        self.running = False
        self.interval = 30.0
        self.deadline = None
        self.notifier = Notifier()

        root = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(6))
        controls = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(5))
        self.folder_input = TextInput(text=self.default_folder(), multiline=False, hint_text='Image directory')
        scan = Button(text='Load', size_hint_x=None, width=dp(75))
        scan.bind(on_release=lambda *_: self.load_folder())
        controls.add_widget(self.folder_input)
        controls.add_widget(scan)
        root.add_widget(controls)

        self.picture = Image(allow_stretch=True, keep_ratio=True)
        root.add_widget(self.picture)
        self.title_label = Label(text='Select a folder and tap Load', size_hint_y=None, height=dp(32), shorten=True)
        root.add_widget(self.title_label)
        self.stats = Label(text='No slideshow loaded', size_hint_y=None, height=dp(54))
        root.add_widget(self.stats)

        options = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(5))
        options.add_widget(Label(text='Seconds:', size_hint_x=None, width=dp(75)))
        self.interval_input = TextInput(text='30', multiline=False, input_filter='float', size_hint_x=None, width=dp(85))
        options.add_widget(self.interval_input)
        self.shuffle_button = Button(text='Shuffle: ON')
        self.shuffle = True
        self.shuffle_button.bind(on_release=self.toggle_shuffle)
        options.add_widget(self.shuffle_button)
        root.add_widget(options)

        actions = GridLayout(cols=3, size_hint_y=None, height=dp(50), spacing=dp(5))
        self.play_button = Button(text='Start')
        self.play_button.bind(on_release=self.toggle_play)
        next_button = Button(text='Next')
        next_button.bind(on_release=lambda *_: self.next_image())
        reshuffle_button = Button(text='Reshuffle')
        reshuffle_button.bind(on_release=lambda *_: self.reshuffle())
        for button in (self.play_button, next_button, reshuffle_button):
            actions.add_widget(button)
        root.add_widget(actions)
        xs = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(250), spacing=dp(3))
        xs.add_widget(Label(text='XScreensaver service controller (system confirmation required)', size_hint_y=None, height=dp(25)))
        self.module_input = TextInput(text='Tap Discover to enumerate installed modules', multiline=False, readonly=True, size_hint_y=None, height=dp(43))
        xs.add_widget(self.module_input)
        self.module_status = Label(text='Module queue is a controller preview; automatic XS module switching is not yet supported.', font_size='12sp')
        xs.add_widget(self.module_status)
        xs_actions = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(3))
        for name, handler in [('Discover', self.discover_xs), ('Next', self.next_xs), ('Timer: OFF', self.toggle_xs_timer), ('Mode', self.toggle_xs_mode)]:
            b = Button(text=name, font_size='12sp')
            b.bind(on_release=handler)
            xs_actions.add_widget(b)
            if name.startswith('Timer:'): self.xs_timer_button = b
        xs.add_widget(xs_actions)
        diag = Button(text='Diagnostics / Android screensaver settings', size_hint_y=None, height=dp(42))
        diag.bind(on_release=self.diagnostic_action)
        xs.add_widget(diag)
        root.add_widget(xs)
        native = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(4))
        for caption, action in [('Background start', 'START'), ('Background stop', 'STOP')]:
            button = Button(text=caption)
            button.bind(on_release=lambda _, a=action: self.native_rotation(a))
            native.add_widget(button)
        root.add_widget(native)
        Clock.schedule_interval(self.tick, 0.25)
        return root

    def native_rotation(self, action):
        if platform != 'android':
            self.module_status.text = 'Android only'
            return
        try:
            from jnius import autoclass
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            intent = autoclass('android.content.Intent')()
            intent.setClassName(activity.getPackageName(), 'org.example.screenflow.RotationService')
            intent.setAction(action)
            if action == 'START':
                self.xs_clock.stop()
                self.xs_timer_button.text = 'Timer: OFF'
                intent.putExtra('interval', int(min(86400, self.read_interval()) * 1000))
                activity.startForegroundService(intent)
                self.module_status.text = 'Background rotation requested; tap notification Apply to confirm.'
            else:
                activity.startService(intent)
                self.module_status.text = 'Background stop requested'
        except Exception as exc:
            self.module_status.text = str(exc)

    def default_folder(self):
        if platform == 'android':
            return '/storage/emulated/0/Pictures'
        return str(Path.home() / 'Pictures')

    def load_folder(self):
        folder = os.path.expanduser(self.folder_input.text.strip())
        if not os.path.isdir(folder):
            self.title_label.text = 'Folder not found or inaccessible'
            return
        self.files = sorted(str(p) for p in Path(folder).iterdir()
                            if p.is_file() and p.suffix.lower() in EXTENSIONS)
        self.index = 0
        self.transitions = 0
        self.started_at = None
        self.running = False
        self.play_button.text = 'Start'
        self.queue = []
        self.current = None
        if not self.files:
            self.picture.source = ''
            self.title_label.text = 'No supported images in folder'
            self.refresh_stats()
            return
        self.reshuffle()
        self.next_image()

    def reshuffle(self):
        self.queue = list(self.files)
        if self.shuffle:
            random.shuffle(self.queue)
            if len(self.queue) > 1 and self.queue[-1] == self.current:
                self.queue[0], self.queue[-1] = self.queue[-1], self.queue[0]
        if self.current in self.queue and len(self.queue) > 1:
            self.queue.remove(self.current)
        self.refresh_stats()

    def toggle_shuffle(self, *_):
        self.shuffle = not self.shuffle
        self.shuffle_button.text = 'Shuffle: ON' if self.shuffle else 'Shuffle: OFF'
        self.reshuffle()

    def next_image(self):
        if not self.files:
            return
        if not self.queue:
            self.reshuffle()
        if not self.queue:
            self.queue = [self.current]
        self.current = self.queue.pop(0)
        self.index += 1
        self.transitions += 1
        self.picture.source = self.current
        self.picture.reload()
        self.title_label.text = os.path.basename(self.current)
        if self.running:
            self.deadline = time.monotonic() + self.interval
        self.refresh_stats()

    def toggle_play(self, *_):
        if not self.files:
            self.load_folder()
        if not self.files:
            return
        if not self.running:
            try:
                self.interval = max(1.0, float(self.interval_input.text))
            except ValueError:
                self.interval = 30.0
                self.interval_input.text = '30'
            if self.started_at is None:
                self.started_at = time.monotonic()
            self.running = True
            self.deadline = time.monotonic() + self.interval
            self.play_button.text = 'Pause'
        else:
            self.running = False
            self.play_button.text = 'Resume'
        self.refresh_stats()

    def discover_xs(self, *_):
        entries = self.bridge.discover(self.xs_mode)
        self.xs_entries = {e['class']: e for e in entries}
        self.xs_queue.load(list(self.xs_entries))
        self.module_input.text = f'{len(entries)} exported {self.xs_mode} services discovered'
        self.module_status.text = ('Discovered %d modules; selected modules are not automatically activated' % len(entries)) if entries else ('No services found. ' + (self.bridge.error or 'Check package installation'))
        self.xs_clock.stop()
        self.xs_timer_button.text = 'Timer: OFF'

    def toggle_xs_mode(self, *_):
        self.xs_mode = 'dream' if self.xs_mode == 'wallpaper' else 'wallpaper'
        self.discover_xs()
        self.module_status.text = 'Mode: ' + self.xs_mode + ' — ' + self.module_status.text

    def next_xs(self, *_):
        klass = self.xs_queue.next()
        if not klass:
            self.module_status.text = 'Discover installed modules first'
            return
        entry = self.xs_entries[klass]
        name = entry['name']
        if self.xs_mode == 'wallpaper':
            ok, result = self.bridge.change_wallpaper(klass)
        else:
            ok, result = self.bridge.open_dream_settings()
        self.module_status.text = '%s (%d/%d): %s' % (name, self.xs_queue.count, len(self.xs_entries), result)
        self.notifier.update('ScreenFlow XS: ' + name, 'Requested #%d · %s · %s' % (self.xs_queue.count, self.xs_mode, 'confirmation pending' if ok else 'request failed'))

    def toggle_xs_timer(self, *_):
        if self.xs_clock.running:
            self.xs_clock.stop()
            self.xs_timer_button.text = 'Timer: OFF'
            return
        if not self.xs_queue.items:
            self.discover_xs()
        if not self.xs_queue.items:
            return
        try:
            seconds = float(self.interval_input.text)
        except ValueError:
            seconds = 60
        self.xs_clock.start(seconds)
        self.xs_timer_button.text = 'Timer: ON'
        self.module_status.text = 'Timer armed; Android confirmation still required for each wallpaper change'

    def diagnostic_action(self, *_):
        from kivy.uix.popup import Popup
        from kivy.uix.scrollview import ScrollView
        report = self.bridge.diagnostics()
        if self.xs_mode == 'dream':
            ok, message = self.bridge.open_dream_settings()
            report += '\nDream settings launch: ' + message
        content = ScrollView()
        label = Label(text=report, size_hint_y=None, halign='left', valign='top', text_size=(dp(290), None))
        label.bind(texture_size=lambda widget, value: setattr(widget, 'height', value[1] + dp(20)))
        content.add_widget(label)
        Popup(title='XScreensaver diagnostics', content=content, size_hint=(0.95, 0.65)).open()

    def load_modules(self, *_):
        self.module_controller.configure(self.module_input.text.split(','))
        self.module_status.text = f'Loaded {len(self.module_controller.modules)} module names (not verified against installed XS)'

    def next_module(self, *_):
        if not self.module_controller.modules:
            self.load_modules()
        name = self.module_controller.next()
        if name:
            self.module_status.text = f'Queued: {name} | #{self.module_controller.count} | XS switching requires adapter'
            self.notifier.update(f'XS queue: {name}', f'Module #{self.module_controller.count} | selection preview only')
        if self.module_running:
            self.module_deadline = time.monotonic() + self.read_interval()

    def read_interval(self):
        try: return max(1., float(self.interval_input.text))
        except (TypeError, ValueError): return 30.

    def toggle_modules(self, *_):
        self.module_running = not self.module_running
        self.module_auto_button.text = 'Auto: ON' if self.module_running else 'Auto: OFF'
        if self.module_running:
            self.module_started = time.monotonic()
            self.next_module()

    def open_xs(self, *_):
        ok, message = self.module_controller.open_xscreensaver()
        self.module_status.text = message

    def tick(self, dt):
        if self.xs_clock.due():
            self.next_xs()
        if self.module_running and self.module_deadline is not None and time.monotonic() >= self.module_deadline:
            self.next_module()

        if self.running and self.deadline is not None and time.monotonic() >= self.deadline:
            self.next_image()
        self.refresh_stats()

    def refresh_stats(self):
        elapsed = int(time.monotonic() - self.started_at) if self.started_at else 0
        remaining = max(0, int(self.deadline - time.monotonic() + 0.99)) if self.running and self.deadline else 0
        status = 'Playing' if self.running else 'Paused'
        self.stats.text = f'{status} | {len(self.files)} images | Shown: {self.transitions} | Elapsed: {elapsed}s | Next: {remaining}s'
        if self.current:
            self.notifier.update(os.path.basename(self.current),
                                 f'{status} · Shown {self.transitions} · {elapsed}s elapsed · {remaining}s next')

    def on_stop(self):
        self.notifier.clear()

if __name__ == '__main__':
    ScreenFlow().run()
