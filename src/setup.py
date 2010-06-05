# python setup.py py2exe

from distutils.core import setup
import py2exe

setup(windows=['mooconsole.py'])

##setup(
##    windows = [
##        {
##            "script": "mooconsole.py",
##            "icon_resources": [(1, "moodle.ico")]
##        }
##    ],
##)