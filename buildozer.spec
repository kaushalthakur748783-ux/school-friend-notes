[app]
title = Class Notes
package.name = classnotes
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
requirements = python3,kivy,kivymd,plyer,pillow
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.permissions = CAMERA, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# Debug में APK बने:
android.debug_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 1
