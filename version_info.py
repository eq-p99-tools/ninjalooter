"""Generate a PyInstaller VSVersionInfo file from config."""
from ninjalooter import config

_M = config.SEMVER.major
_m = config.SEMVER.minor
_p = config.SEMVER.patch
_V = config.VERSION

VERSION_INFO_TEMPLATE = f"""\
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({_M}, {_m}, {_p}, 0),
    prodvers=({_M}, {_m}, {_p}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
           StringStruct(u'CompanyName',
                        u'NinjaLooter'),
           StringStruct(u'FileDescription',
                        u'NinjaLooter - EQ Loot Tracker'),
           StringStruct(u'FileVersion',
                        u'{_V}'),
           StringStruct(u'InternalName',
                        u'ninjalooter'),
           StringStruct(u'LegalCopyright',
                        u'NinjaLooter Contributors'),
           StringStruct(u'OriginalFilename',
                        u'ninjalooter-{_V}.exe'),
           StringStruct(u'ProductName',
                        u'NinjaLooter'),
           StringStruct(u'ProductVersion',
                        u'{_V}'),
          ])
      ]),
    VarFileInfo([VarStruct(u'Translation',
                           [1033, 1200])])
  ]
)
"""

if __name__ == '__main__':
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(VERSION_INFO_TEMPLATE)
    print(f"Wrote version_info.txt for v{config.VERSION}")
