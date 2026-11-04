[app]
title = Piyasa Gözü
package.name = piyasagozu
package.domain = com.piyasagozu
source.dir = .
source.include_exts = py,txt,png,jpg,kv
version = 1.0.0
requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.0,requests,certifi,urllib3,idna,chardet
orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 33
android.minapi = 23
android.ndk = 25b
android.ndk_api = 23
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.enable_androidx = True
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
