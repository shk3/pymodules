.. pymodules documentation master file, created by
   sphinx-quickstart on Tue Oct  9 08:50:31 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pymodules's documentation!
=====================================

PyModules is an alternative implementation of the
`Environment Modules <http://modules.sourceforge.net/>`_ system
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
`Center for Computation and Visualization <http://ccv.brown.edu/>`_
at Brown University, and distributed under a non-commercial, open-source
license (see below). The latest source code is available from the git repository at:

  `<https://bitbucket.org/mhowison/pymodules>`_

Stable releases are also available as zip archives from:

  `<https://bitbucket.org/mhowison/pymodules/downloads>`_


Citing
======

Howison M, Shen A, Loomis A. 2013. `Building Software Environments for Research Computing Clusters <https://www.usenix.org/conference/lisa13/technical-sessions/papers/howison>`_. In Proceedings of the 27th Large Installation System Administration Conference (LISA '13), Washington, DC, USA.


Contents
========

.. toctree::
   :maxdepth: 2

   install
   modulefiles


Authors
=======

| Mark Howison
| Andy Loomis
| Aaron Shen


License
=======

::

    PyModules - Software Environments for Research Computing Clusters
    
    Copyright 2012-2013, Brown University, Providence, RI. All Rights Reserved.
    
    This file is part of PyModules.
    
    Permission to use, copy, modify, and distribute this software and its
    documentation for any purpose other than its incorporation into a
    commercial product is hereby granted without fee, provided that the
    above copyright notice appear in all copies and that both that
    copyright notice and this permission notice appear in supporting
    documentation, and that the name of Brown University not be used in
    advertising or publicity pertaining to distribution of the software
    without specific, written prior permission.
    
    BROWN UNIVERSITY DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
    INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR ANY
    PARTICULAR PURPOSE.  IN NO EVENT SHALL BROWN UNIVERSITY BE LIABLE FOR
    ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

