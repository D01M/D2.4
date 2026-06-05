# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for OpenSeismo Lite desktop application
Bundles Flask server, web UI, and all dependencies into a single executable
"""

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('Index-Globe.html', '.'),
        ('index.html', '.'),
        ('intensity_calculator.py', '.'),
        ('tsunami_warning.py', '.'),
        ('location_search.py', '.'),
        ('live_earthquake_detector.py', '.'),
    ],
    hiddenimports=[
        'flask',
        'requests',
        'werkzeug',
        'jinja2',
        'click',
        'itsdangerous',
        'markupsafe',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OpenSeismo Lite',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OpenSeismo Lite',
)
