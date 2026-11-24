"""Safe XScreensaver handoff adapter. No undocumented module-switch API is assumed."""
import random
from kivy.utils import platform

class ModuleController:
    def __init__(self):
        self.modules = []
        self.queue = []
        self.current = None
        self.count = 0
        self.shuffle = True

    def configure(self, names):
        self.modules = list(dict.fromkeys(s.strip() for s in names if s.strip()))
        self.queue = []
        self.current = None
        self.count = 0

    def next(self):
        if not self.modules:
            return None
        if not self.queue:
            self.queue = list(self.modules)
            if self.shuffle:
                random.shuffle(self.queue)
                if len(self.queue) > 1 and self.queue[0] == self.current:
                    self.queue[0], self.queue[-1] = self.queue[-1], self.queue[0]
        self.current = self.queue.pop(0)
        self.count += 1
        return self.current

    def open_xscreensaver(self):
        """Open installed XScreensaver app, without claiming automatic module control."""
        if platform != 'android':
            return False, 'Android only'
        try:
            from jnius import autoclass
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            pm = activity.getPackageManager()
            # Package ID must be verified against the installed APK on target device.
            for pkg in ('org.jwz.android.xscreensaver',):
                intent = pm.getLaunchIntentForPackage(pkg)
                if intent is not None:
                    activity.startActivity(intent)
                    return True, 'Opened XScreensaver; select module in its UI'
            return False, 'XScreensaver launch activity not found; check installed package ID'
        except Exception as exc:
            return False, str(exc)
