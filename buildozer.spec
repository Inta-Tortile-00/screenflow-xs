[app]
title = ScreenFlow XS Controller
package.name = screenflow
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,json,java,xml
version = 0.5.2
requirements = python3,kivy,pyjnius
orientation = portrait
fullscreen = 0
android.minapi = 28
android.api = 33
android.permissions = READ_EXTERNAL_STORAGE,FOREGROUND_SERVICE,SET_WALLPAPER,POST_NOTIFICATIONS
android.add_src = android_src
android.add_resources = android_res
p4a.hook = manifest_hook.py
#android.extra_manifest_application_arguments = service_manifest.xml
#android.extra_manifest_xml = queries.xml
android.archs = arm64-v8a,armeabi-v7a
android.ndk = 25b
[buildozer]
log_level = 2
warn_on_root = 1
