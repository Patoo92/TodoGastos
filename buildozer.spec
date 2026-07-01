[app]
title = To-Do & Gastos
package.name = todogastos
package.domain = org.tienclimatek
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy
orientation = portrait
presplash.filename = icon.png
icon.filename = icon.png
osx.python_version = 3
osx.kivy_version = 2.2.0
fullscreen = 0

android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.gradle_dependencies =
android.accept_sdk_license = True
android.arch = arm64-v8a
android.private_storage = True
android.permissions =

[buildozer]
log_level = 2
warn_on_root = 1
