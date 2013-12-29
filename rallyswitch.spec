# -*- mode: python -*-
a = Analysis(['rallyswitch.py'],
             #pathex=['/Users/rwooden/Dropbox/projects/jira-thinggy'],
             hiddenimports=[],
             hookspath=['./hooks/'],
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='rallyswitch',
          debug=False,
          strip=None,
          upx=True,
          console=True )
