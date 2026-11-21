# ScreenFlow XS — GitHub Actions APK build

This package includes the original v0.3.0 sources plus `.github/workflows/android-apk.yml`.

## Setup from Windows 11 (no Android SDK required)
1. Sign in to GitHub and create a **private** repository named `screenflow-xs`. Initialize it with no README.
2. Unzip this package locally.
3. Upload **the contents** of the extracted folder to the root of the repository, including the hidden `.github/workflows/android-apk.yml` file. GitHub's web uploader can upload files, but handling hidden nested directories can be awkward; the simplest reliable approach is GitHub Desktop or Git CLI.
4. In the repository, open **Actions** → **Build ScreenFlow Android APK** → **Run workflow** → **Run workflow**.
5. After a successful run, open the run page, scroll to **Artifacts**, download `screenflow-xs-debug-apk`, and unzip it to obtain the APK.

## Git CLI alternative
From inside the extracted project folder:

    git init
    git branch -M main
    git add .
    git commit -m "Add ScreenFlow XS Android build"
    git remote add origin https://github.com/YOUR_USERNAME/screenflow-xs.git
    git push -u origin main

The push automatically starts the workflow. Replace YOUR_USERNAME with your GitHub account name.

## Troubleshooting
- First builds download SDK/NDK and can take a while; check Actions logs.
- The toolchain has not been run or verified in this environment; dependency/version changes may require adjustments.
- This is a **debug APK**. It is not Play Store-ready and has not been tested on Fire OS.
- A debug build is normally signed with a development key; do not treat it as a production release.
- The controller requests wallpaper changes using Android system UI; it does not bypass user confirmation.
- The current version does not have a persistent Android foreground service.
