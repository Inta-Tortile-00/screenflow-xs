[app]
title = ScreenFlow XS Controller
package.name = screenflow
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv
version = 0.3.0
requirements = python3,kivy,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE
android.archs = arm64-v8a,armeabi-v7a
android.sdk_path = /usr/local/lib/android/sdk
android.api = 33
android.minapi = 28
android.ndk = 25b
android.accept_sdk_license = True
android.skip_update = True

[buildozer]
log_level = 2
warn_on_root = 1
