from setuptools import setup

APP = ['ping-menubar.py']
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'LSUIElement': True,
        'LSBackgroundOnly': True,  
        'CFBundleIdentifier': 'com.example.ping-menubar',
        'CFBundleShortVersionString': '1.1.0',
        'CFBundleVersion': '1.1.0', 
    },
    'packages': ['Foundation', 'AppKit'],
}

setup(
    app=APP,
    setup_requires=['py2app'],
    options={'py2app': OPTIONS},
)
