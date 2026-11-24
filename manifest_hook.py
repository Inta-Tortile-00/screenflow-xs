"""p4a before_apk_build hook: patch cached distribution template, idempotently."""
from pathlib import Path
import re

SERVICE = '''<service android:name="org.example.screenflow.RotationService" android:exported="false" android:process=":rotation" />
<service android:name="org.example.screenflow.WallpaperAccessibilityService" android:label="ScreenFlow wallpaper automation" android:exported="true" android:process=":rotation" android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">
<intent-filter><action android:name="android.accessibilityservice.AccessibilityService" /></intent-filter>
<meta-data android:name="android.accessibilityservice" android:resource="@xml/wallpaper_accessibility" />
</service>'''

def before_apk_build(toolchain):
    # p4a runs this hook in its packaging phase; locate the selected distribution.
    root = Path(__file__).resolve().parent
    paths = list((root / '.buildozer/android/platform').glob('build-*/dists/screenflow/**/AndroidManifest.tmpl.xml'))
    if not paths:
        raise RuntimeError('ScreenFlow: cached AndroidManifest.tmpl.xml not found')
    for path in paths:
        text = path.read_text()
        text = re.sub(r'<service\b[^>]*android:name="org\.example\.screenflow\.RotationService"[^>]*/>', '', text)
        if 'org.example.screenflow.WallpaperAccessibilityService' not in text:
            text = text.replace('</application>', SERVICE+'\n</application>', 1)
        else:
            text = text.replace('</application>', SERVICE.split('\n')[0]+'\n</application>', 1)
        if 'org.jwz.android.xscreensaver' not in text:
            package = '<package android:name="org.jwz.android.xscreensaver" />'
            if '</queries>' in text: text=text.replace('</queries>',package+'</queries>',1)
            else: text=text.replace('</manifest>','<queries>'+package+'</queries></manifest>',1)
        path.write_text(text)
        print('ScreenFlow manifest:',path)
