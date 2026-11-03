[app]
title = Piyasa Gözü
package.name = piyasagozu
package.domain = com.piyasagozu
source.dir = .
source.include_exts = py,txt,png,jpg,kv
version = 1.0.0
requirements = python3,kivy,requests
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[app]
android.permissions = INTERNET
android.api = 35
android.minapi = 23
android.ndk_api = 23
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.enable_androidx = True
p4a.bootstrap = sdl2
