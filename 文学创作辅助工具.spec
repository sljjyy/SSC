# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('prompts', 'prompts')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter.test', 'tkinter.test.test_tkinter', 'tkinter.test.test_tkinter.test_widgets', 'tkinter.test.test_tkinter.test_variables', 'tkinter.test.test_ttk', 'tkinter.test.test_ttk.test_extensions', 'tkinter.test.test_ttk.test_functions', 'tkinter.test.test_ttk.test_style', 'tkinter.test.test_ttk.test_widgets', 'unittest', 'pdb', 'pydoc'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='文学创作辅助工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
