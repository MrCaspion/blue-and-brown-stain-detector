from setuptools import setup
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.py')
dotStuff_path = os.path.join(script_dir, 'dotStuff.py')
default_params_path = os.path.join(script_dir, 'default_params.json')

APP = ['main.py']
DATA_FILES = [
    config_path,
    dotStuff_path,
    default_params_path
]

FRAMEWORKS = []
if sys.platform == 'darwin':
    if os.path.exists('/System/Library/Frameworks/Tk.framework'):
        FRAMEWORKS.append('/System/Library/Frameworks/Tk.framework')
    if os.path.exists('/System/Library/Frameworks/Tcl.framework'):
        FRAMEWORKS.append('/System/Library/Frameworks/Tcl.framework')

OPTIONS = {
    'argv_emulation': False,
    'packages': ['numpy', 'scipy', 'skimage', 'PIL', 'pandas', 'tkinter', 'cv2'],
    'includes': ['tkinter', 'tkinter.filedialog', 'PIL._tkinter_finder', 'scipy', 'cv2'],
    'excludes': ['matplotlib', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6'],
    'frameworks': FRAMEWORKS,
    'site_packages': True,
    'resources': ['config.py', 'dotStuff.py', 'default_params.json'],
    'iconfile': None,
    'plist': {
        'CFBundleName': 'Biology Image Analysis',
        'CFBundleDisplayName': 'Biology Image Analysis',
        'CFBundleGetInfoString': 'Tool for biological image analysis',
        'CFBundleIdentifier': 'com.user.biologyimageanalysis',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2023',
        'NSHighResolutionCapable': True,
    }
}

setup(
    app=APP,
    name="Biology Image Analysis",
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app>=0.14'],
    version="1.0",
)