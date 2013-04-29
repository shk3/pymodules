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

import ConfigParser
import os
import pickle
import sys
import sqlite3 as sqlite

from modulecfg import *
from moduleutil import splitid, simdize, info, print_columns


class ModuleError(Exception):
    """ Base class for all module exceptions """
    def __init__(self, msg, type=None):
        super(ModuleError,self).__init__(msg)
        self.warning = msg + messages.get(type, '')

    def warn(self):
        """ Print a warning message. """
        print >>sys.stderr, "module: warning:", self.warning


class Module:
    """ Encapsulates all of the logic for manipulating a module """

    def __init__(self,modulefile):
        """ Initializes a module from a modulefile """

        self.name = os.path.basename(modulefile)
        self.defaults = defaults.copy()
        self.defaults['name'] = self.name

        config = ConfigParser.SafeConfigParser(self.defaults)
        config.optionxform = str

        try:
            config.read(modulefile)
        except ConfigParser.MissingSectionHeaderError:
            raise ModuleError("no versions specified in '%s'" % modulefile)
        except ConfigParser.ParsingError as e:
            raise ModuleError(
                    "error parsing modulefile '%s'\n%s" % (
                    modulefile, e))

        sections = config.sections()
        if not sections:
            raise ModuleError("no versions specified in '%s'" % modulefile)
        self.default_version = config.get(sections[0],'version');

        self.versions = []
        self.actions = {}
        self.data = {}
        self.paths = {}

        for section in sections:

            version = config.get(section,'version')
            self.versions.append(version)
            if config.getboolean(section,'default'):
                self.default_version = version

            try:
                self.actions[version] = []
                self.data[version] = {}
                self.paths[version] = []
                for key,val in config.items(section):
                    if key.partition(' ')[0] in ('set', 'append', 'prepend'):
                        if '"' in val:
                            raise ModuleError("found illegal '\"' character in action for '%s':\n  %s = %s" % (modulefile,key,val)) 
                        self.actions[version].append((key,val))
                        if key.partition(' ')[2] == 'PATH':
                            self.paths[version] += val.split(':')
                    else:
                        self.data[version][key] = val

            except ConfigParser.InterpolationError as e:
                raise ModuleError(
                        "error interpreting modulefile '%s'\n  %s" % (
                        modulefile, str(e)))

        self.versions.sort()


    def help(self,version=None):
        """ Prints helpful information about this module """

        version = self.__pick_version(version)
        print >>sys.stderr, \
            '\nName:     ', self.name, \
            '\nVersions: ', ', '.join(self.versions), \
            '\nDefault:  ', self.default_version, \
            '\nURL:      ', self.data[version].get('url', ''), \
            '\nBrief:    ', self.data[version].get('brief', ''), \
            '\n\n', self.data[version].get('usage', '')
        if 'loadmsg' in self.data[version]:
            print >>sys.stderr, \
               "\nLoad Message:\n%s" % self.data[version]['loadmsg']


    def show(self,env,version=None):
        """ Prints the environment changes to standard error """

        version = self.__pick_version(version)
        for key,val in self.actions[version]:
            action = key.split(' ',1)
            if action[0] == 'set': env.set(action[1],val)
            elif action[0] == 'append': env.append(action[1],val)
            elif action[0] == 'prepend': env.prepend(action[1],val)
        
        env.append(LOADEDMODULES,'/'.join([self.name,version]))


    def load(self,env,version=None):
        """ Loads this module and modifies the caller's environment """

        self.unload(env)

        version = self.__pick_version(version)

        info("loading '%s/%s'" % (self.name, version))
        if 'loadmsg' in self.data[version]:
            print >>sys.stderr, \
                "module: %s: %s" % (
                self.name, self.data[version]['loadmsg'])

        for key,val in self.actions[version]:
            action = key.split(' ',1)
            if action[0] == 'set': env.set(action[1],val)
            elif action[0] == 'append': env.append(action[1],val)
            elif action[0] == 'prepend': env.prepend(action[1],val)

        env.append(LOADEDMODULES,'/'.join([self.name,version]))


    def unload(self,env,strict=False):
        """ Unloads this module and resets the caller's environment """

        version = self.__pick_loaded()
        if not version:
            if strict:
                raise ModuleError("'%s' is not currently loaded" % self.name)
            else:
                return # Fail silenty

        info("unloading '%s/%s'" % (self.name, version))

        for key,val in self.actions[version]:
            action = key.split(' ',1)
            if action[0] == 'set':
                env.unset(action[1])
            elif action[0] == 'append':
                for item in val.split(':'):
                    env.remove(action[1],item)
            elif action[0] == 'prepend':
                for item in val.split(':'):
                    env.remove(action[1],item)

        env.remove(LOADEDMODULES,'/'.join([self.name,version]))


    def list_bin(self,version):
        """ List the executables provided by the module. """

        version = self.__pick_version(version)

        # Lambda function tests if a path is an executable file
        is_exe = lambda f: os.path.isfile(f) and os.access(f, os.X_OK)

        for path in self.paths[version]:
            path = simdize(path)
            os.chdir(path)
            programs = filter(is_exe, os.listdir(path))
            if programs:
                print >>sys.stderr, "%s:" % path
                print_columns(sorted(programs))


    def __pick_version(self,version):
        """ Picks the version of the module based on the request """

        if not version:
            return self.default_version
        elif not version in self.versions:
            raise ModuleError(
                "unknown version '%s/%s'" % (self.name, version),
                type='unknown')
        else: return version


    def __pick_loaded(self):
        """ Picks the version of the module based on the loaded modules """

        moduleids = os.getenv(LOADEDMODULES)
        if moduleids:
            for moduleid in moduleids.split(':'):
                name,version = splitid(moduleid)
                if name == self.name:
                    return version
        return None


class ModuleDb:
    """ Encapsulates the database of modules """

    def __init__(self):
        self.conn = None
        self.connect()


    def connect(self, dbfile=MODULEDB):
        """ Initializes connections to the sqlite database """
        try:
            if self.conn:
                self.conn.close()
            self.conn = sqlite.connect(dbfile, isolation_level=None)
        except sqlite.OperationalError as e:
            raise ModuleError(
                "can't connect to database '%s' (sqlite3 error: %s)" % (
                dbfile, e))
        self.conn.row_factory = sqlite.Row


    def rebuild(self,path):
        """ Rebuilds the database with the modulefiles in the path """

        # Since rebuild can take some time, write the new database to a
        # temporary path to prevent service interruption.
        tmpfile = MODULEDB + '~'
        if os.path.exists(tmpfile):
            os.unlink(tmpfile)

        self.connect(tmpfile)

        self.conn.execute("""
            CREATE TABLE modules (
                name TEXT PRIMARY KEY,
                data BLOB)""")

        self.conn.execute("""
            CREATE TABLE moduleids (
                name TEXT,
                version TEXT,
                PRIMARY KEY (name,version))""")

        self.conn.execute("""
            CREATE TABLE categories (
                category TEXT,
                name TEXT,
                version TEXT,
                PRIMARY KEY (category,name,version))""")

        for modulefile in os.listdir(path):
            if not modulefile.startswith('.'):
                self.insert(os.path.join(path,modulefile))

        # Move temporary database in place ...
        self.conn.close()
        os.chmod(tmpfile, moduleperm)
        os.rename(tmpfile, MODULEDB)

        # ... and reestablish the connection.
        self.connect()


    def insert(self,modulefile,force=False):
        """ Inserts the modulefile as a Module into the database """

        try:
            module = Module(modulefile)
        except ModuleError as e:
            e.warn()
            return

        blob = sqlite.Binary(pickle.dumps(module,pickle.HIGHEST_PROTOCOL))

        self.conn.execute('BEGIN')

        if force:
            self.conn.execute(
                "REPLACE INTO modules VALUES (?,?)",
                (module.name,blob))
            self.conn.execute(
                "DELETE FROM moduleids WHERE name = ?",
                (module.name,))
            self.conn.execute(
                "DELETE FROM categories WHERE name = ?",
                (module.name,))
        else:
            try:
                self.conn.execute(
                    "INSERT INTO modules VALUES (?,?)",
                    (module.name,blob))
            except sqlite.IntegrityError:
                raise ModuleError(
                        "duplicate module already in database for '%s'" % \
                        module.name)
        
        for version in module.versions:
            self.conn.execute(
                "INSERT INTO moduleids VALUES (?,?)",
                (module.name,version))
            for category in module.data[version].get('category', '(none)').split(','):
                self.conn.execute(
                    "INSERT INTO categories VALUES (?,?,?)",
                    (category,module.name,version))
            
        self.conn.execute('COMMIT')

        os.chmod(modulefile, moduleperm)


    def lookup(self,name):
        """ Return the module with the specified name from the database """

        cursor = self.conn.execute("""
            SELECT name, data
            FROM modules
            WHERE name = ?""",(name,))

        result = cursor.fetchone()
        if result: return pickle.loads(str(result['data']))
        else: raise ModuleError("unknown module '%s'" % name, 'unknown')


    def avail(self,name='',version=''):
        """ Return a list of the modules in the database matching the
            specified name and version. """

        cursor = self.conn.execute("""
            SELECT name, version
            FROM moduleids
            WHERE name LIKE ? AND version LIKE ?
            ORDER BY name """,
            (name+'%','%'+version+'%'))
        return map('/'.join, cursor)


    def avail_category(self,category=''):
        """ Return a list of modules organized by category. """

        cursor = self.conn.execute("""
            SELECT category, name, version
            FROM categories
            WHERE category LIKE ? 
            ORDER BY category, name """,
            (category+'%',))
        category = None
        matches = []
        for row in cursor:
            if row[0] != category:
                category = row[0]
                matches.append((category, []))
            matches[-1][1].append(row[1]+'/'+row[2])
        return matches


class ModuleEnv:
    """ Encapsulates an environment that multiple modules can alter """

    def __init__(self):
        self._env = dict()
        self._env_unset = set()


    def get(self,variable):
        """ Gets an environment variable from the cache """

        try:
            return self._env[variable]
        except KeyError:
            return os.getenv(variable)


    def dump(self,out=sys.stdout):
        """ Prints the environment variable cache line by line """

        if MODULESHELL == 'bash':
            unsetfmt = "unset {0};"
            setfmt = "export {0}=\"{1}\";"
        elif MODULESHELL == 'csh':
            unsetfmt = "unsetenv {0};"
            setfmt = "setenv {0} \"{1}\";"
        else:
            raise NotImplementedError(MODULESHELL)

        for var in self._env_unset:
            print >>out, unsetfmt.format(var)
        for var,val in self._env.iteritems():
            print >>out, setfmt.format(var,val)


    def set(self,variable,value):
        """ Sets the environment variable to the specified value """

        if variable == 'MANPATH' and value[-1] != ':':
            value += ':'
        self._env[variable] = value


    def unset(self,variable,value=None):
        """ Unsets/resets the environment variable to the specified value """

        self._env_unset.add(variable)
        if value: self.set(variable,value)


    def append(self,variable,path):
        """ Appends the path to the environment variable """

        path = simdize(path)
        paths = self.get(variable)
        if not paths:
            paths = path
        else:
            paths = paths.split(':')
            paths = [x for x in paths if x != path]
            paths.append(path)
            paths = ':'.join(paths)
        self.set(variable,paths)


    def prepend(self,variable,path):
        """ Prepends the path to the environment variable """

        path = simdize(path)
        paths = self.get(variable)
        if not paths:
            paths = path
        else:
            paths = paths.split(':')
            paths = [x for x in paths if x != path]
            paths.insert(0,path)
            paths = ':'.join(paths)
        self.set(variable,paths)


    def remove(self,variable,path):
        """ Removes the path from the environment variable """

        path = simdize(path)
        paths = self.get(variable)
        if paths:
            paths = paths.split(':')
            paths = [x for x in paths if x != path]
            paths = ':'.join(paths)
            self.set(variable,paths)


# vim:ts=4:shiftwidth=4:expandtab:
