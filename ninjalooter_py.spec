# -*- mode: python -*-

block_cipher = None

datas = [('data/icons', 'data/icons')]
datas += [('data/sounds/*.mp3', 'data/sounds')]
datas += [('data/items.json', 'data/items.json')]
datas += [('data/spells.json', 'data/spells.json')]

a = Analysis(['ninjalooter\\cmd\\run.py'],
             pathex=[],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
from ninjalooter import config
CONSOLE_BUILD = bool(config.SEMVER.build)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='ninjalooter-%s' % config.VERSION,
          debug=CONSOLE_BUILD,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          console=CONSOLE_BUILD,
          icon='data/icons/ninja_attack.ico')

import zipfile
import os

os.chdir('dist')
zipfile.ZipFile(f"ninjalooter-{config.VERSION}.zip", "w", zipfile.ZIP_DEFLATED).write(f"ninjalooter-{config.VERSION}.exe")
os.chdir("..")
