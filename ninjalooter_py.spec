# -*- mode: python -*-

block_cipher = None


a = Analysis(['ninjalooter\\cmd\\run.py'],
             pathex=['D:\\rm-you.github.com\\ninjalooter'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher
)
from glob import glob
a.datas += [(filename, filename, '.') for filename in glob('data/*')]
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='ninjalooter',
          debug=True,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          console=True,
          icon='data/ninja_attack.ico')
