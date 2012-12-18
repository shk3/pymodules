import argparse
import sys
import os

from module import ModuleError, Module, ModuleDb, ModuleEnv
from modulecfg import LOADEDMODULES
from moduleutil import splitid, print_centered, print_columns, set_verbose, info


def avail(args):
    """ Print a list of available modules. """

    moduledb = ModuleDb()
    if not args.module:
        matches = sorted(moduledb.avail(verbose=args.verbose))
        print_columns(matches)
    else:
        for moduleid in args.module:
            name,version = splitid(moduleid)
            matches = moduledb.avail(name,version,args.verbose)
            print_columns(matches)


def list_loaded(args):
    """ Print a list of loaded modules. """

    moduleids = os.getenv(LOADEDMODULES)
    if not moduleids:
        return

    moduleids = [m for m in moduleids.split(':') if m]
    print_columns(moduleids)


def load(args):
    """ Load modules. """

    env = ModuleEnv()
    db = ModuleDb()
    for moduleid in args.module:
        name,version = splitid(moduleid)
        try:
            Module.load(db.lookup(name),env,version)
        except ModuleError as e:
            e.warn()
    env.dump()


def unload(args):
    """ Unload modules. """

    env = ModuleEnv()
    db = ModuleDb()
    for moduleid in args.module:
        name,version = splitid(moduleid)
        try:
            Module.unload(db.lookup(name),env,strict=True)
        except ModuleError as e:
            e.warn()
    env.dump()


def show(args):
    """ Show environment changes from modules. """

    env = ModuleEnv()
    db = ModuleDb()
    for moduleid in args.module:
        name,version = splitid(moduleid)
        try:
            Module.show(db.lookup(name),env,version)
        except ModuleError as e:
            e.warn()
    env.dump(sys.stderr)


def help(args):
    """ Print help message for module. """

    # Doesn't use ModuleEnv or Module
    name,version = splitid(args.module)
    try:
        ModuleDb().lookup(name).help(version)
    except ModuleError as e:
        e.warn()


def alias_subcommand(argv):
    """ Substitute aliases for each command """

    i = 1 # subcommand is at argument index 1
    if len(argv) > i:
        if argv[i] in ('add','switch','swap'): argv[i] = 'load'
        elif argv[i] in ('rm','remove'): argv[i] = 'unload'
        elif argv[i] == 'display': argv[i] = 'show'
        elif argv[i] == 'whatis': argv[i] = 'help'


def main():

    parser = argparse.ArgumentParser(prog='modulecmd')
    parser.add_argument('-v','--verbose',action='store_true');

    subparsers = parser.add_subparsers(title='subcommands')

    avail_parser = subparsers.add_parser('avail')
    avail_parser.add_argument('-v','--verbose',action='store_true');
    avail_parser.add_argument('module',nargs='*')
    avail_parser.set_defaults(func=avail)

    load_parser = subparsers.add_parser('load', help="aliases: add switch swap")
    load_parser.add_argument('module',nargs='+')
    load_parser.set_defaults(func=load)

    unload_parser = subparsers.add_parser('unload', help="aliases: rm remove")
    unload_parser.add_argument('module',nargs='+')
    unload_parser.set_defaults(func=unload)

    list_parser = subparsers.add_parser('list')
    list_parser.set_defaults(func=list_loaded)

    show_parser = subparsers.add_parser('show', help="aliases: display")
    show_parser.add_argument('module',nargs='+')
    show_parser.set_defaults(func=show)

    help_parser = subparsers.add_parser('help', help="aliases: whatis")
    help_parser.add_argument('module')
    help_parser.set_defaults(func=help)

    alias_subcommand(sys.argv)
    args = parser.parse_args()
    if args.verbose: set_verbose()
    args.func(args)


if __name__ == '__main__':
    main()

# vim:ts=4:shiftwidth=4:expandtab:
