import sys
import argparse

from module import ModuleError, ModuleDb
from modulecfg import MODULEPATH

def _rebuild(args):
    # Rebuild the module database from modulefiles in the path

    moduledb = ModuleDb()
    try:
        moduledb.rebuild(args.modulepath)
    except ModuleError as e:
        e.warn()


def _insert(args):
    # Insert each modulefile into the database

    moduledb = ModuleDb()
    for modulefile in args.modulefile:
        try:
            moduledb.insert(modulefile,args.force)
        except ModuleError as e:
            e.warn()


def main():

    parser = argparse.ArgumentParser(prog='moduledb')
    subparsers = parser.add_subparsers(title='subcommands')

    rebuild_parser = subparsers.add_parser('rebuild')
    rebuild_parser.add_argument('modulepath',nargs='?',default=MODULEPATH)
    rebuild_parser.set_defaults(func=_rebuild)

    insert_parser = subparsers.add_parser('insert')
    insert_parser.add_argument('-f','--force',action='store_true');
    insert_parser.add_argument('modulefile',nargs='+')
    insert_parser.set_defaults(func=_insert)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()

# vim:ts=4:shiftwidth=4:expandtab:
