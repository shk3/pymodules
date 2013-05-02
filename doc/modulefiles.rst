Writing `modulefiles`
=====================

A `modulefile` is an INI-style configuration file with `key = value` pairs
that specify how a software module will modify the user's environment when
loaded.

Any value you define can also be referenced by another value using the syntax
`%(key)s` (the standard syntax used by the Python INI parser).

The most common usage of this is to create a path based on the default
module hierarchy using the `rootdir` value, which expands to::

  /{module-root}/{module-name}/{module-version}

Basic fields
------------

All modulefiles define at least two INI sections: the first is `[DEFAULT]` and
contains key/values pairs inherited by all versions of the package. At least
one other section must be defined to provide a version. The fields `brief` (a
brief description of the package) and an `url` (to a location where the user can
lookup more information about the package), should also be provided in the
default section. Here is an example of a minimal modulefile::

  [DEFAULT]
  
  brief = A brief description of the package
  url = http://url/to/package/homepage
  
  [1.2.3]

The `name` field is automatically set to the filename of the modulefile.

Inserting into the database
---------------------------

Once a modulefile is ready, use the command::

  moduledb insert <filename>

to insert it into the database. This will generate an error if the module
already exists. To update an existing module, add the `-f` flag to force the
insert command::

  moduledb insert -f <filename>

Rebuilding the entire database
------------------------------

To rebuild a new database from all modulefiles in the `MODULEPATH`, use the
command::

  moduledb rebuild

This builds a new database at a temporary location (which can take on the order
of seconds or minutes if you have hundreds of modulefiles), then copies it over
the existing database.  This way, the live copy of the database won't become
corrupt during the rebuild.  However, no locking is conducted, so another
administrator's modification of the existing database could be lost.

Localization
------------

Fully optimizing the software environment to take advantage of the different
architectures in a heterogenous research cluster requires localized
installations that are specific to each CPU architecture. PyModules supports
localized installations of software at three levels, from coarsest to finest:
by vender, SIMD instruction set, or processor model.

Vendor
~~~~~~

At the coarsest level, the variable `%%VENDOR%%` in a modulefile path is
replaced at load time with either `intel` or `amd` depending on the
architecture of the node. For instance, this makes it possible to install two
versions of a software package that depends on BLAS, one linked against ACML
that will load on nodes with AMD processors and another linked against MKL
that will load on those with Intel processors.

SIMD
~~~~

At a finer level, the variable `%%SIMD%%` is replaced at load time with the
highest SIMD instruction set supported by the node. This allows software
to take advantage of an advanced vector instruction if it is available on a
node, or otherwise to fall back to a version that works on all nodes.

At runtime, PyModules inspects the host machine for the highest avaiable SIMD
instruction set it supports, from the following list (in order)::

  avx
  sse4.2
  sse4a
  sse3
  . (default)

This value is substituted for the special variable `%%SIMD%%` in a modulefile,
allowing for multiple optimized builds to live in the same module.

As an example, consider the `examples/blast` modulefile that comes with
PyModules. It species the following PATH::

  prepend PATH = %(rootdir)s/%%SIMD%%/bin

On an Intel Sandy Bridge machine, this would expand to::

  prepend PATH = %(rootdir)s/avx/bin

On an Intel Nehalem::

  prepend PATH = %(rootdir)s/sse4.2/bin

On an AMD Barcelona::

  prepend PATH = %(rootdir)s/sse4a/bin

Or on any older machine that doesn't even support SSE3::

  prepend PATH = %(rootdir)s/./bin

An example file tree for a blast module could look like::

  .
  ..
  avx -> sse4.2
  bin
  sse3 -> .
  sse4.2
  sse4a -> .

In this case, an optimized version has been built with SSE4.2 instructions, and
will also be used by AVX machines. Meanwhile, an SSE4a, SSE3, or pre-SSE3
machine would use the default installation in the root directory.

Model
~~~~~

At the finest level, the variable `%%MODEL%%` is replaced at load time by a
string that identifies the precise model of processor on the node. This can
be used when installing software packages that, like the ATLAS or GotoBLAS
libraries, use autotuning to optimize themselves at build time for a specific
processor model.

The `%%MODEL%%` variable is replaced by a triplet `<vendor>-<cpu
family>-<model>` that is read from the `/proc/cpuinfo` interface, for example
`intel-6-26`.

To figure our the model keyword for a given system, use `more /proc/cpuinfo`
and look for entries like these::

  vendor_id	: GenuineIntel
  cpu family	: 6
  model		: 26

