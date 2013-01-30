Writing `modulefiles`
=====================

A `modulefile` is an INI-style configuration file with `key = value` pairs
that specify how a software module will modify the user's environment when
loaded.

Any value you define can also be referenced by another value using the syntax::

  %(key)s

The most common usage of this is to create a path based on the default
module hierarchy using the `rootdir` value, which expands to::

  /{module-root}/{module-name}/{module-version}


SIMD Architecture
-----------------

`pymodules` has built-in support for modules that will be loaded on
heterogenous hardware and need to be optimized for different levels of
SIMD instructions.

At runtime, `pymodules` inspects the host machine for the highest avaiable SIMD
instruction set it supports, from the following list (in order)::

  avx
  sse4.2
  sse4a
  sse3
  . (default)

This value is substituted for the special variable `%%SIMD%%` in a modulefile,
allowing for multiple optimized builds to live in the same module.

As an example, consider the `blast` modulefile that comes with `pymodules`. It
species the following PATH::

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

