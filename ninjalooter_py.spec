# -*- mode: python -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(SPEC)))

from version_info import VERSION_INFO_TEMPLATE
from ninjalooter import config

# Write version info for this build
with open('version_info.txt', 'w', encoding='utf-8') as _vf:
    _vf.write(VERSION_INFO_TEMPLATE)

datas = [('data/icons', 'data/icons')]
datas += [('data/sounds/*.mp3', 'data/sounds')]
datas += [('data/items.json', 'data')]
datas += [('data/spells.json', 'data')]

a = Analysis(['ninjalooter\\cmd\\run.py'],
             pathex=[],
             binaries=[],
             datas=datas,
             hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
)

pyz = PYZ(a.pure, a.zipped_data)

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
          icon='data/icons/ninja_attack.ico',
          version='version_info.txt')

import zipfile
import os

os.chdir('dist')
zipfile.ZipFile(
    f"ninjalooter-{config.VERSION}.zip", "w", zipfile.ZIP_DEFLATED
).write(f"ninjalooter-{config.VERSION}.exe")
os.chdir("..")
