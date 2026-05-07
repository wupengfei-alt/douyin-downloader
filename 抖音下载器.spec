# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['douyin_downloader_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # 核心依赖
        'f2.cli',
        'f2.cli.dy',
        'f2.handlers',
        'f2.models',
        'f2.utils',
        'rich',
        'rich.console',
        'rich.table',
        'rich.panel',
        'rich.progress',
        'requests',
        'urllib3',
        'charset_normalizer',
        'certifi',
        # Playwright 相关
        'playwright',
        'playwright.sync_api',
        'pyee',
        'websockets',
        'wsproto',
        'h2',
        'hpack',
        'hyperframe',
        'async_timeout',
        'attrs',
        'outcome',
        'sniffio',
        'typing_extensions',
        # Tkinter
        '_tkinter',
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.filedialog',
        'tkinter.messagebox',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['IPython', 'jedi', 'parso', 'black', 'pygments'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='抖音下载器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version=None,
    uac_admin=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='抖音下载器',
)
