import argparse
import sys
import os

from module import ModuleError, Module, ModuleDb, ModuleEnv
from modulecfg import LOADEDMODULES
from moduleutil import splitid, print_centered, print_columns


def avail(args):
    """
    List available modules.
    """

    moduledb = ModuleDb()
    if not args.module:
        args.module = [':']
    for moduleid in args.module:
        name,version = splitid(moduleid)
        if name.startswith(':'):
            for category, matches in moduledb.avail_category(name[1:]):
                print_centered('category: ' + category)
                print_columns(matches)
        else:
            title = 'name: %s*/*' % name
            if version:
                title = '%s%s*' % (title, version)
            print_centered(title)
            print_columns(moduledb.avail(name,version))


def list_loaded(args):
    """
    List currently loaded modules.
    """

    moduleids = os.getenv(LOADEDMODULES)
    if not moduleids:
        return

    moduleids = [m for m in moduleids.split(':') if m]
    print_columns(moduleids)


def load(args):
    """
    Load modules, unloading any versions that are already loaded.
    aliases: add switch swap
    """

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
    """
    Unload modules, if the specified version is already loaded.
    aliases: rm remove
    """

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
    """
    Show the environment changes that will be made when loading the module.
    aliases: display
    """

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
    """
    Print additional information about a module.
    aliases: whatis
    """

    # Doesn't use ModuleEnv or Module
    name,version = splitid(args.module)
    try:
        ModuleDb().lookup(name).help(version)
    except ModuleError as e:
        e.warn()


def list_bin(args):
    """ 
    List the programs provided by the module.
    """

    db = ModuleDb()
    for moduleid in args.module:
        name,version = splitid(moduleid)
        try:
            Module.list_bin(db.lookup(name),version)
        except ModuleError as e:
            e.warn()


def alias_subcommand(argv):
    """
    Substitute aliases for each command.
    """

    i = 1 # subcommand is at argument index 1
    if len(argv) > i:
        if argv[i] in ('add','switch','swap'): argv[i] = 'load'
        elif argv[i] in ('rm','remove'): argv[i] = 'unload'
        elif argv[i] == 'display': argv[i] = 'show'
        elif argv[i] == 'whatis': argv[i] = 'help'


def main():

    parser = argparse.ArgumentParser(prog='modulecmd')

    subparsers = parser.add_subparsers(title='subcommands')

    avail_parser = subparsers.add_parser('avail', help=avail.__doc__)
    avail_parser.add_argument('module',nargs='*')
    avail_parser.set_defaults(func=avail)

    load_parser = subparsers.add_parser('load', help=load.__doc__)
    load_parser.add_argument('module',nargs='+')
    load_parser.set_defaults(func=load)

    unload_parser = subparsers.add_parser('unload', help=unload.__doc__)
    unload_parser.add_argument('module',nargs='+')
    unload_parser.set_defaults(func=unload)

    list_parser = subparsers.add_parser('list', help=list_loaded.__doc__)
    list_parser.set_defaults(func=list_loaded)

    show_parser = subparsers.add_parser('show', help=show.__doc__)
    show_parser.add_argument('module',nargs='+')
    show_parser.set_defaults(func=show)

    help_parser = subparsers.add_parser('help', help=help.__doc__)
    help_parser.add_argument('module')
    help_parser.set_defaults(func=help)

    bin_parser = subparsers.add_parser('bin', help=list_bin.__doc__)
    bin_parser.add_argument('module',nargs='+')
    bin_parser.set_defaults(func=list_bin)

    alias_subcommand(sys.argv)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()

# vim:ts=4:shiftwidth=4:expandtab:
