# -*- mode: python -*-
a = Analysis(['issueswitch.py'],
             hiddenimports=[],
             hookspath=['./hooks/'],
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='issueswitch',
          debug=False,
          strip=None,
          upx=True,
          console=True )
