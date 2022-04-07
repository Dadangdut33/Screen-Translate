# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['ScreenTranslate.py'],
             pathex=['./'],
             binaries=[],
             datas=[
                ('./user_manual', 'user_manual'),
                ('./img_captured', 'img_captured'),
                ('./json', 'json'),
                ('./user_manual/Readme.txt', '.'),
                ('./user_manual/Changelog.txt', '.'),
                ('./logo.ico', '.'),
                ('./logo.png', '.'),
             ],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['pyinstaller'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='ScreenTranslate',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , icon='logo.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='ScreenTranslate 1.8.5 No Console')
