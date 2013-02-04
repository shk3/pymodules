import ConfigParser
import os
import pickle
import sys
import sqlite3 as sqlite

from modulecfg import *
from moduleutil import splitid, get_simd_flag, info


class ModuleError(Exception):
    """ Base class for all module exceptions """
    def __init__(self, msg, type=None):
        super(ModuleError,self).__init__(msg)
        self.warning = msg + messages.get(type, '')

    def warn(self):
        """ Print a warning message. """
        print >>sys.stderr, "module: warning: %s" % self.warning


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

        for section in sections:

            version = config.get(section,'version')
            self.versions.append(version)
            if config.getboolean(section,'default'):
                self.default_version = version

            try:
                self.actions[version] = []
                self.data[version] = {}
                for key,val in config.items(section):
                    if key.partition(' ')[0] in ('set', 'append', 'prepend'):
                        if '"' in val:
                            raise ModuleError("found illegal '\"' character in action for '%s':\n  %s = %s" % (modulefile,key,val)) 
                        self.actions[version].append((key,val))
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
                env.unset(action[1],val)
            elif action[0] == 'append':
                for item in val.split(':'):
                    env.remove(action[1],item)
            elif action[0] == 'prepend':
                for item in val.split(':'):
                    env.remove(action[1],item)

        env.remove(LOADEDMODULES,'/'.join([self.name,version]))


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
        """ Initializes connections to the sqlite database """
        try:
            self.conn = sqlite.connect(MODULEDB)
        except sqlite.OperationalError as e:
            raise ModuleError(
                "can't connect to database '%s' (sqlite3 error: %s)" % (
                MODULEDB, e))
        self.conn.row_factory = sqlite.Row


    def rebuild(self,path):
        """ Rebuilds the database with the modulefiles in the path """

        # Since rebuild can take some time, write the new database to a
        # temporary path to prevent service interruption.
        tmpfile = MODULEDB + '~'
        if os.path.exists(tmpfile):
            os.unlink(tmpfile)

        self.conn.close()
        self.conn = sqlite.connect(tmpfile)

        self.conn.execute("""
            CREATE TABLE modules (
                name TEXT PRIMARY KEY,
                data BLOB)""")

        self.conn.execute("""
            CREATE TABLE moduleids (
                name TEXT,
                version TEXT,
                PRIMARY KEY (name,version))""")

        for modulefile in os.listdir(path):
            if not modulefile.startswith('.'):
                self.insert(os.path.join(path,modulefile))

        # Move temporary database in place ...
        self.conn.close()
        os.chmod(tmpfile, moduleperm)
        os.rename(tmpfile, MODULEDB)

        # ... and reestablish the connection.
        self.conn = sqlite.connect(MODULEDB)
        self.conn.row_factory = sqlite.Row


    def insert(self,modulefile,force=False):
        """ Inserts the modulefile as a Module into the database """

        try:
            module = Module(modulefile)
        except ModuleError as e:
            e.warn()
            return

        blob = sqlite.Binary(pickle.dumps(module,pickle.HIGHEST_PROTOCOL))

        if force:
            self.conn.execute(
                "REPLACE INTO modules VALUES (?,?)",
                (module.name,blob))
            self.conn.execute(
                "DELETE FROM moduleids WHERE name = ?",
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

        self.conn.commit()

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


    def unset(self,variable,value):
        """ Unsets/resets the environment variable to the specified value """

        self._env_unset.add(variable)
        if value: self.set(variable,value)


    def append(self,variable,path):
        """ Appends the path to the environment variable """

        path = self.__simdize(path)
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

        path = self.__simdize(path)
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

        path = self.__simdize(path)
        paths = self.get(variable)
        if paths:
            paths = paths.split(':')
            paths = [x for x in paths if x != path]
            paths = ':'.join(paths)
            self.set(variable,paths)


    def __simdize(self,val):
        """
        Replace the special value %SIMD% in a path with the appropriate
        SSE instruction level of the current machine.
        """

        if self._simd is None:
            self._simd = get_simd_flag()

        return val.replace('%SIMD%', self._simd)


# vim:ts=4:shiftwidth=4:expandtab:
