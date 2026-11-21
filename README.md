# ScreenFlow XS Controller 0.3.0 — source prototype

Android 9 / Fire OS 7-oriented Kivy project. This is source, **not a compiled or device-tested APK**.

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
