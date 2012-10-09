import ConfigParser
import os
import pickle
import sys
import sqlite3 as sqlite

from modulecfg import defaults, MODULEDB, MODULESHELL, LOADEDMODULES, messages
from moduleutil import splitid, get_simd_flag


class ModuleError(Exception):
    """ Base class for all module exceptions """
    def __init__(self, msg, type=None):
        super(ModuleError,self).__init__(msg)
        self.warning = msg + messages.get(type, '')

    def warn(self):
        """ Print a warning message. """
        print >> sys.stderr, "%s: warning: %s" % (__name__, self.warning)


class Module:
    """ Encapsulates all of the logic for manipulating a module """

    def __init__(self,modulefile):
        """ Initializes a module from a modulefile """

        config = ConfigParser.SafeConfigParser(defaults)
        config.optionxform = str

        try:
            config.read(modulefile)
        except ConfigParser.ParsingError:
            raise ModuleError("error parsing modulefile '%s'" % modulefile)
        except ConfigParser.MissingSectionHeaderError:
            raise ModuleError("no versions specified in '%s'" % modulefile)

        sections = config.sections()
        if not sections:
            raise ModuleError("no versions specified in '%s'" % modulefile)
        self.default_version = config.get(sections[0],'version');

        try:
            self.name = config.get(self.default_version,'name')
        except ConfigParser.NoOptionError:
            raise ModuleError("missing required 'name' in '%s'" % modulefile)

        self.versions = []
        self.actions = dict()
        for section in sections:

            self.versions.append(config.get(section,'version'))
            if config.getboolean(section,'default'):
                self.default_version = self.versions[-1]

            try:
                self.actions[self.versions[-1]] = dict(config.items(section))
            except ConfigParser.InterpolationError as e:
                raise ModuleError("error interpolating modulefile '%s'\n  %s" % (modulefile, str(e)))

        self.versions.sort()


    def help(self,version=None):
        """ Prints helpful information about this module """

        version = self.__pick_version(version)
        print >>sys.stderr, \
            'Name:', self.name, '\n', \
            'Versions:', ', '.join(self.versions), '\n', \
            'Default:', self.default_version, '\n\n', \
            self.actions[version]['brief'], '\n\n', \
            self.actions[version]['usage']


    def show(self,env,version=None):
        """ Prints the environment changes to standard error """

        version = self.__pick_version(version)
        for key in self.actions[version].keys():
            action = key.split(' ',1)
            if action[0] == 'set':
                env.set(action[1],self.actions[version][key])
            elif action[0] == 'append':
                env.append(action[1],self.actions[version][key])
            elif action[0] == 'prepend':
                env.prepend(action[1],self.actions[version][key])
        
        env.append(LOADEDMODULES,'/'.join([self.name,version]))


    def load(self,env,version=None):
        """ Loads this module and modifies the caller's environment """

        self.unload(env)

        version = self.__pick_version(version)
        for key in self.actions[version].keys():
            action = key.split(' ',1)
            if action[0] == 'set':
                env.set(action[1],self.actions[version][key])
            elif action[0] == 'append':
                env.append(action[1],self.actions[version][key])
            elif action[0] == 'prepend':
                env.prepend(action[1],self.actions[version][key])

        env.append(LOADEDMODULES,'/'.join([self.name,version]))


    def unload(self,env,version=None):
        """ Unloads this module and resets the caller's environment """

        version = self.__pick_loaded()
        if not version:
            return # Fail silently

        for key in self.actions[version].keys():
            action = key.split(' ',1)
            if action[0] == 'set':
                env.unset(action[1],self.actions[version][key])
            elif action[0] == 'append':
                env.remove(action[1],self.actions[version][key])
            elif action[0] == 'prepend':
                env.remove(action[1],self.actions[version][key])

        env.remove(LOADEDMODULES,'/'.join([self.name,version]))


    def __pick_version(self,version):
        """ Picks the version of the module based on the request """

        if not version:
            return self.default_version
        elif not version in self.versions:
            raise ModuleError(
                "unknown version '%s/%s'" % (self.name, version),
                'unknown')
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
        """ Initializes connections to the sqlite database """
        self.conn = sqlite.connect(MODULEDB)
        self.conn.row_factory = sqlite.Row


    def __del__(self):
        """ Closes connections to the sqlite database """
        self.conn.close()


    def rebuild(self,path):
        """ Rebuilds the database with the modulefiles in the path """

        self.conn.execute("DROP TABLE IF EXISTS modules")
        self.conn.execute("""
            CREATE TABLE modules (
                name TEXT PRIMARY KEY,
                data BLOB)""")

        self.conn.execute("DROP TABLE IF EXISTS moduleids")
        self.conn.execute("""
            CREATE TABLE moduleids (
                name TEXT,
                version TEXT,
                PRIMARY KEY (name,version))""")

        for modulefile in os.listdir(path):
            if not modulefile.startswith('.'):
                self.insert(os.path.join(path,modulefile))


    def insert(self,modulefile,force=False):
        """ Inserts the modulefile as a Module into the database """

        module = Module(modulefile)
        blob = sqlite.Binary(pickle.dumps(module,pickle.HIGHEST_PROTOCOL))

        if force:
            self.conn.execute("REPLACE INTO modules VALUES (?,?)",
                (module.name,blob))
            self.conn.execute("DELETE FROM moduleids WHERE name = ?",
                (module.name,))
        else:
            try:
                self.conn.execute("INSERT INTO modules VALUES (?,?)",
                    (module.name,blob))
            except sqlite.IntegrityError:
                raise ModuleError("duplicate module already in database for '%s'" % module.name)
        
        for version in module.versions:
            self.conn.execute("INSERT INTO moduleids VALUES (?,?)",
                (module.name,version))

        self.conn.commit()


    def lookup(self,name):
        """ Return the module with the specified name from the database """

        cursor = self.conn.execute("""
            SELECT name, data
            FROM modules
            WHERE name = ?""",(name,))

        result = cursor.fetchone()
        if result: return pickle.loads(str(result['data']))
        else: raise ModuleError("unknown module '%s'" % name, 'unknown')


    def avail(self,name='',version='',verbose=False):
        """ Return a list of the modules in the database matching the
            specified name and version. """

        if not verbose:
            cursor = self.conn.execute("""
                SELECT name
                FROM modules
                WHERE name LIKE ?""",(name+'%',))
            modules = [module['name'] for module in cursor]
        else:
            cursor = self.conn.execute("""
                SELECT name, version
                FROM moduleids
                WHERE name LIKE ? AND version LIKE ? """,
                (name+'%','%'+version+'%'))
            modules = [module['name']+'/'+module['version'] for module in cursor]

        return modules


class ModuleEnv:
    """ Encapsulates an environment that multiple modules can alter """

    def __init__(self):
        self._env = dict()
        self._env_unset = set()
        self._simd = None


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
            setfmt = "export {0}={1};"
        elif MODULESHELL == 'csh':
            unsetfmt = "unsetenv {0};"
            setfmt = "setenv {0} {1};"
        else:
            raise NotImplementedError(MODULESHELL)

        if self._simd is None:
            self._simd = get_simd_flag()

        for var in self._env_unset:
            print >>out, unsetfmt.format(var)
        for var,val in self._env.iteritems():
            print >>out, setfmt.format(var,val.replace('%SIMD%', self._simd))


    def set(self,variable,value):
        """ Sets the environment variable to the specified value """

        self._env[variable] = value


    def unset(self,variable,value):
        """ Unsets/resets the environment variable to the specified value """

        self._env_unset.add(variable)
        if value: self.set(variable,value)


    def append(self,variable,path):
        """ Appends the path to the environment variable """

        paths = self.get(variable)
        if paths is None:
            paths = path
        else:
            paths = paths.split(':')
            paths = [x for x in paths if x != path]
            paths.append(path)
            paths = ':'.join(paths)
        self.set(variable,paths)


    def prepend(self,variable,path):
        """ Prepends the path to the environment variable """

        paths = self.get(variable)
        if paths is None:
            paths = path
        else:
            paths = paths.split(':')
            paths = [x for x in paths if x != path]
            paths.insert(0,path)
            paths = ':'.join(paths)
        self.set(variable,paths)


    def remove(self,variable,path):
        """ Removes the path from the environment variable """

        paths = self.get(variable)
        if paths:
            paths = paths.split(':')
            paths = [x for x in paths if x != path]
            paths = ':'.join(paths)
            self.set(variable,paths)


# vim:ts=4:shiftwidth=4:expandtab:
