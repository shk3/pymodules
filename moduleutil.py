#
# PyModules - Software Environments for Research Computing Clusters
#
# Copyright 2012-2013, Brown University, Providence, RI. All Rights Reserved.
#
# This file is part of PyModules.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose other than its incorporation into a
# commercial product is hereby granted without fee, provided that the
# above copyright notice appear in all copies and that both that
# copyright notice and this permission notice appear in supporting
# documentation, and that the name of Brown University not be used in
# advertising or publicity pertaining to distribution of the software
# without specific, written prior permission.
#
# BROWN UNIVERSITY DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
# INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR ANY
# PARTICULAR PURPOSE.  IN NO EVENT SHALL BROWN UNIVERSITY BE LIABLE FOR
# ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


import os
import sys
import subprocess


_localized = None


def splitid(moduleid):
    """ Return the module and name from the moduleid """
    
    moduleid = moduleid.split('/',1)
    if len(moduleid) == 1:
        moduleid.append('')
    return moduleid[0],moduleid[1]


def print_centered(string,term_width=80,pad_char='~'):
    """ Print a string centered in the terminal """

    print >>sys.stderr, (' '+string+' ').center(term_width,pad_char)


def print_columns(moduleids,term_width=80):
    """ Print a list of strings in columns """

    if not moduleids: return;

    # Calculate the number of columns based on the longest string
    column_width = max(len(moduleid) for moduleid in moduleids)+2
    num_columns = term_width/column_width
    column_length = (len(moduleids)+num_columns-1)/num_columns

    # Pad the moduleid with spaces
    moduleids = [moduleid.ljust(column_width) for moduleid in moduleids]

    # Print in columns
    for i in range(column_length):
        line = ''
        for j in range(num_columns):
            k = j*column_length+i
            if k < len(moduleids):
                line += moduleids[k]
        print >>sys.stderr, line


def localize(path):
    """
    Replace the special value `%SIMD%` in `path` with the highest SSE
    instruction level of the current machine, in the set:

        (`avx`, `sse4.2`, `sse4a`, `sse3`, `.`)

    And the special value `%VENDOR$` with either `intel`, `amd`, or `.`.

    Note: only works on Linux, since values are read from `/proc/cpuinfo`.
    """
    global _localized

    if not _localized:
        _localized = { 'vendor': '.', 'simd': '.', 'model': '.' }
        if os.path.exists('/proc/cpuinfo'):
            try:
                model = []
                for line in open('/proc/cpuinfo'):
                    line = line.rstrip().split()
                    if line[0] == 'vendor_id':
                        if line[2] == 'GenuineIntel':
                            _localized['vendor'] = 'intel'
                        elif line[2] == 'AuthenticAMD':
                            _localized['vendor'] = 'amd'
                        model.append(_localized['vendor'])
                    elif line[0] == 'cpu' and line[1] == 'family':
                        model.append(line[-1])
                    elif line[0] == 'model' and line[1] == ':':
                        model.append(line[-1])
                    elif line[0] == 'flags':
                        flags = set(line[2:])
                        if 'avx' in flags:
                            _localized['simd'] = 'avx'
                        elif 'sse4_2' in flags:
                            _localized['simd'] = 'sse4.2'
                        elif 'sse4a' in flags:
                            _localized['simd'] = 'sse4a'
                        elif 'sse3' in flags:
                            _localized['simd'] = 'sse3'
                        # No more lines need to be read.
                        break

                # Only set model if all three fields are found.
                if len(model) == 3 and model[0] != '.':
                    _localized['model'] = '-'.join(model)

            except:
                print >>sys.stderr, \
                    "module: warning: couldn't parse /proc/cpuinfo"

    return path.replace('%VENDOR%', _localized['vendor']) \
               .replace('%SIMD%', _localized['simd']) \
               .replace('%MODEL%', _localized['model'])


def info(msg):
    """
    Print an informational message to stderr, prefixed with "module: ".
    """
    print >>sys.stderr, "module:", msg


# vim:ts=4:shiftwidth=4:expandtab:
