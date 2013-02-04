import os

# Environment variables.

MODULEPATH = os.environ['MODULEPATH']
MODULEDB = os.path.join(MODULEPATH, '.db.sqlite')
MODULESHELL = os.environ['MODULESHELL']
LOADEDMODULES = 'LOADEDMODULES'

# Default data.

defaults = {
    'rootdir': '/gpfs/runtime/opt/%(name)s/%(__name__)s',
    'version': '%(__name__)s',
    'default': 'false'
}

messages = {
	'unknown': """
  Please contact CCV support (support@ccv.brown.edu) if you think that software
  with this module name should be installed."""
}

# Forces all modulefiles to have group-writable permissions: important if you
# plan to have multiple users maintaining modulefiles and updating the
# database. NOTE: you must include the leading 0 in the octal code!
moduleperm = 0664

