# ScreenFlow XS Controller 0.4.0 — source prototype

Android 9 / Fire OS 7-oriented Kivy project. This is source, **not a compiled or device-tested APK**.

<img width="1200" height="1920" alt="Screenshot_20261123-182207" src="https://github.com/user-attachments/assets/9787ab05-f861-4614-b0fc-f3ece077b700" />

## Features
- Existing local-image slideshow with interval, pause, next, shuffle and notification.
- Android PackageManager discovery of exported `WallpaperService` and `DreamService` components in `org.jwz.xscreensaver`.
- Two XS modes: wallpaper selection via Android `ACTION_CHANGE_LIVE_WALLPAPER`, and Daydream settings via `android.settings.DREAM_SETTINGS`.
- No-repeat module queue, manual next, optional interval-driven requests, and current selection notification.
- Diagnostics popup reporting installed package version and discoverable service counts.

## Important limits
- Wallpaper change opens the **system confirmation UI**. ScreenFlow does not silently apply the wallpaper, and its notifications report *requested*, not *active*.
- Android DreamService is not publicly switchable on demand by a third-party app. Dream mode opens Android settings; selecting an individual dream is manual.
- Kivy Clock runs **only while the application process is alive and its event loop is running**. This release does not contain an Android foreground service, so it does not promise reliable background scheduling, nor does it provide a genuine Android live-wallpaper service.
- A timer repeatedly launching confirmation UI can be intrusive. Start with a long interval and test manual Next first.
- On Fire OS, system activities may be missing or blocked. Use Diagnostics to confirm availability.
- PackageManager results may differ from the static APK candidates; the runtime discovery results are authoritative.
- The uploaded APK was inspected for candidate class-name strings, not fully decompiled; `module_candidates.json` is informational only.

## Build
On Linux with Java, Android SDK/NDK and Buildozer installed:

    buildozer -v android debug

Find APK under `bin/`. `android.api=33`, `android.minapi=28`; Android 9 is the minimum supported OS target. This build configuration has **not** been verified on a device. Kivy/p4a compatibility may require Buildozer toolchain updates.

## Files
- `main.py`: Kivy slideshow and controller UI
- `android_bridge.py`: Android public API integration
- `queue_engine.py`: shuffle and timer logic
- `xs_controller.py`: legacy queue helper retained for compatibility
- `module_candidates.json`: APK-derived class-name candidates (not verified exported services)
- `buildozer.spec`: Android build configuration

## Diagnostic workflow
1. Install XScreensaver 6.15 and ScreenFlow.
2. Open ScreenFlow; tap Discover in wallpaper mode.
3. Tap Next and check whether Fire OS opens the correct confirmation screen.
4. Switch to Dream mode; Discover; open diagnostics/settings.
5. Report discovery counts and any errors before enabling timed requests.

## v0.4.0 experimental native rotation
Corrected package ID; class names are discovered from PackageManager. Background start uses the Seconds field and starts a separate Java foreground service. Tap Apply in its notification to open the system wallpaper confirmation; Next selects another candidate, Pause toggles scheduling, Stop ends the service. Queue and selection count persist. Timer is best effort during sleep; no boot receiver or silent live wallpaper changes. Local slideshow remains in the original Kivy UI. Native Android compilation and device testing are not yet verified. On Android 13 notification permission may need to be granted in settings. Fire OS 7 does not require that runtime permission.

## v0.5.0 experimental accessibility rotation

Enable ScreenFlow wallpaper automation in Android Accessibility settings, return to ScreenFlow, enable Auto XPath and press Background start. The primary selector is extracted from the supplied Automate flow. The optional secondary selector is `(//android.widget.ListView[@android:id='@android:id/list']/android.widget.RelativeLayout)[4]`; leave blank until you have manually verified the fourth row is the desired destination. The XScreensaver app's own apply button is not clicked by this version: it uses the direct system preview instead. Only the system picker is inspected, during a pending rotation. Locked or sleeping devices skip automatic attempts; the notification Apply remains available. Background activity launches may be restricted by Fire OS. Auto settings are applied when Background start is pressed. Stop or Pause cancels pending clicks. Selection count is not a verified application count; verification is logged when available.

Build with the existing environment and `buildozer -v android debug`. The experimental p4a hook registers both services in the cached manifest template; `android.add_resources` supplies the accessibility XML. Verify generated manifest with xmllint and inspect service declarations. If hook timing or resource handling differs in your p4a version, report the build log. Python syntax checked; Android compilation/device behavior not tested here.

Diagnostics: `adb logcat -s ScreenFlow AndroidRuntime`.

### v0.5.1
- Interval input is in minutes (0.5–1440), default 1; requests a numeric keyboard with decimal input.
- App settings are saved privately in settings.json, automatically and via Save settings. Restart background rotation to apply edits to the native service.
- Only the primary wallpaper XPath is executed; secondary selector removed. Picker still takes foreground focus.
- Existing native rotation state is retained; UI settings start with defaults on first upgrade.

## v0.5.5 standalone screensaver
After installing, grant the optional permission with `adb shell pm grant org.example.screenflow android.permission.WRITE_SECURE_SETTINGS`. Start XS background rotation to populate the upcoming queue snapshot. Load Screensaver Now selects the matching DreamService and launches SystemUI Somnambulator. The system screensaver selection persists; the wallpaper queue is not consumed by this action. If launch throws an exception, the previous selection is restored where possible. ADB success does not guarantee app-level launch permission.
