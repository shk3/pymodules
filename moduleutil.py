import sys
import subprocess

_verbose = False

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


def get_simd_flag():
    """
    Lookup the latest SIMD instruction supported on the current machine, in
    the set ('avx', 'sse4.2', 'sse4a', 'sse3', '.').
    """

    flags = subprocess.Popen(
                ['grep', '-m', '1', 'flags', '/proc/cpuinfo'],
                stdout=subprocess.PIPE).communicate()[0]
    if ' avx ' in flags:
        return 'avx'
    elif ' sse4_2 ' in flags:
        return 'sse4.2'
    elif ' sse4a ' in flags:
        return 'sse4a'
    elif ' sse3 ' in flags:
        return 'sse3'
    else:
        return '.'

def info(msg):
    """
    Print an informational message to stderr, prefixed with "module: ".
    """
    global _verbose
    if _verbose:
        print >>sys.stderr, "module:", msg

def set_verbose():
    """
    Enable verbose messages using the info() utility function.
    """
    global _verbose
    _verbose = True
    info("verbose output enabled")

# vim:ts=4:shiftwidth=4:expandtab:
