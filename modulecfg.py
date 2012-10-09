import os

defaults = {
    'rootdir': '/gpfs/runtime/opt/%(name)s/%(__name__)s',
    'version': '%(__name__)s',
    'default': 'false',
    'brief': '',
    'usage': ''
}

MODULEPATH = os.environ['MODULEPATH']
MODULEDB = os.path.join(MODULEPATH, '.db.sqlite')
MODULESHELL = os.environ['MODULESHELL']
LOADEDMODULES = 'LOADEDMODULES'

messages = {
	'unknown': """
  Please contact CCV support (support@ccv.brown.edu) if you think that software
  with this module name should be installed."""
}
