"""Android 9 public-API bridge. No silent wallpaper changes or privileged APIs."""
import json
from pathlib import Path

PKG = 'org.jwz.xscreensaver'
WALLPAPER_ACTION = 'android.service.wallpaper.WallpaperService'
DREAM_ACTION = 'android.service.dreams.DreamService'

class AndroidBridge:
    def __init__(self):
        self.available = False
        self.error = ''
        try:
            from kivy.utils import platform
            if platform != 'android':
                self.error = 'Android device required for service discovery'
                return
            from jnius import autoclass
            self.J = autoclass
            self.activity = autoclass('org.kivy.android.PythonActivity').mActivity
            self.pm = self.activity.getPackageManager()
            self.Intent = autoclass('android.content.Intent')
            self.ComponentName = autoclass('android.content.ComponentName')
            self.available = True
        except Exception as e:
            self.error = repr(e)

    def discover(self, mode):
        """Return verified exported services via PackageManager; empty if unavailable."""
        if not self.available:
            return []
        action = WALLPAPER_ACTION if mode == 'wallpaper' else DREAM_ACTION
        found = {}
        try:
            intent = self.Intent(action)
            intent.setPackage(PKG)
            results = self.pm.queryIntentServices(intent, 0)
            for entry in results:
                si = entry.serviceInfo
                if str(si.packageName) == PKG and bool(si.exported):
                    found[str(si.name)] = str(si.name).split('$')[-1]
        except Exception as e:
            self.error = 'Discovery: ' + repr(e)
        return sorted(({'name': name, 'class': klass} for klass, name in found.items()), key=lambda v: v['name'].lower())

    def verify_candidate(self, klass):
        """Check whether a named service is installed and exported."""
        if not self.available:
            return False
        try:
            comp = self.ComponentName(PKG, klass)
            info = self.pm.getServiceInfo(comp, 0)
            return bool(info.exported)
        except Exception:
            return False

    def change_wallpaper(self, klass):
        """Launch SYSTEM confirmation UI; NEVER imply wallpaper was applied."""
        if not self.available:
            return False, self.error
        if not self.verify_candidate(klass):
            return False, 'Wallpaper service not found or not exported'
        try:
            intent = self.Intent('android.service.wallpaper.CHANGE_LIVE_WALLPAPER')
            intent.putExtra('android.service.wallpaper.extra.LIVE_WALLPAPER_COMPONENT', self.ComponentName(PKG, klass))
            self.activity.startActivity(intent)
            return True, 'Opened Android wallpaper confirmation; tap Set wallpaper'
        except Exception as e:
            return False, 'Change wallpaper intent failed: ' + repr(e)

    def open_dream_settings(self):
        if not self.available:
            return False, self.error
        try:
            intent = self.Intent('android.settings.DREAM_SETTINGS')
            self.activity.startActivity(intent)
            return True, 'Opened Android screensaver settings; selection is manual'
        except Exception as e:
            return False, 'Dream settings unavailable: ' + repr(e)

    def diagnostics(self):
        if not self.available:
            return self.error
        try:
            package = self.pm.getPackageInfo(PKG, 0)
            ver = str(package.versionName)
        except Exception as e:
            ver = 'not visible / not installed: ' + repr(e)
        w = self.discover('wallpaper')
        d = self.discover('dream')
        return 'Package: %s\nVersion: %s\nExported wallpaper services: %s\nExported dream services: %s\nNote: changing live wallpaper requires system confirmation.\nLast error: %s' % (PKG, ver, len(w), len(d), self.error or 'none')
