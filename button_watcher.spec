# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

root = Path(SPECPATH)
datas = [
    (str(root / "ui" / "styles.qss"), "ui"),
    (str(root / "resources" / "icon.ico"), "resources"),
]
hiddenimports = [
    "playwright.async_api",
    "playwright._impl._driver",
    "playwright._impl._transport",
]

analysis_excludes = [
    "PySide6.QtNetwork", "PySide6.QtOpenGL", "PySide6.QtPdf",
    "PySide6.QtQml", "PySide6.QtQmlMeta", "PySide6.QtQmlModels",
    "PySide6.QtQmlWorkerScript", "PySide6.QtQuick", "PySide6.QtSvg",
    "PySide6.QtVirtualKeyboard",
    "concurrent.futures.process", "concurrent.futures.interpreter",
    "concurrent.interpreters", "multiprocessing",
]

unused_qt_dlls = {
    "qt6network.dll", "qt6opengl.dll", "qt6pdf.dll", "qt6quick.dll",
    "qt6qml.dll", "qt6qmlmeta.dll", "qt6qmlmodels.dll",
    "qt6qmlworkerscript.dll", "qt6svg.dll", "qt6virtualkeyboard.dll",
    "opengl32sw.dll",
}
a = Analysis(
    ["main.py"],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=analysis_excludes,
    noarchive=False,
)

def keep_entry(entry):
    name = entry[0].replace("\\", "/").lower()
    basename = name.rsplit("/", 1)[-1]

    if basename in unused_qt_dlls:
        return False
    if "/translations/" in name:
        return False
    if "/plugins/" in name and not (
        name.endswith("/plugins/platforms/qwindows.dll")
        or name.endswith("/plugins/imageformats/qico.dll")
        or name.endswith("/plugins/styles/qmodernwindowsstyle.dll")
    ):
        return False
    if name.startswith("playwright/driver/package/lib/vite/"):
        return False
    if name.startswith("playwright/driver/package/types/"):
        return False
    return True

a.binaries = [entry for entry in a.binaries if keep_entry(entry)]
a.datas = [entry for entry in a.datas if keep_entry(entry)]

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ButtonWatcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=["python3.dll", "_uuid.pyd"],
    console=False,
    icon=str(root / "resources" / "icon.ico"),
)
