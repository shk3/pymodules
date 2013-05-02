PyModules is an alternative implementation of the
[Environment Modules](http://modules.sourceforge.net/) system
for managing software environments on research computing clusters.
It provides several new features:

* Uses simple, INI-style configuration files that share common values across
  multiple versions of a package.
* Module configuations are cached in a SQLite database, and editing/publishing
  are separate actions.
* Modules can be categorized. The `module avail` command lists by
  category or by fulltext search on the package name or version.
* Modules can be localized by CPU architecture, for either a specific vendor
  (AMD vs. Intel), SSE instruction set, or CPU model identifier.
* New `module bin` command lists all binaries provided by a module.

PyModules is developed by the
[Center for Computation and Visualization](http://ccv.brown.edu/)
at Brown University, and distributed under a non-commercial, open-source
license (see the LICENSE file for full details).

## Documentation

See [http://ccv.brown.edu/mhowison/pymodules](http://ccv.brown.edu/mhowison/pymodules)

For installation instructions, see the INSTALL file.

## Citing

No citation is available yet. We currently have a paper submitted to the USENIX
Large Installation System Administration Conference.

## Issues

Please report any issues using the issue tracker at Bitbucket:

[https://bitbucket.org/mhowison/pymodules/issues](https://bitbucket.org/mhowison/pymodules/issues)

## Authors
Mark Howison  
Andy Loomis

