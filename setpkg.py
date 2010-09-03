"""
An environment variable management system written in python.  The system is
based around .pykg files: python scripts executed in a special environment and
containing python ini-style configuration headers.

Managing Packages
=================

When setting a package, it will be skipped if:
    - a specific version is not requested and a version of the package is already set
    - the requested version is already set



pykg files
==========

Typically, a single .pykg file is written for each application to be managed,
and placed on the SETPKG_PATH. When adding a package using the setpkg module or
command line tool, if the requested version of the package has not yet already
been set, the .pykg file is executed. Differences per OS, architecture, application
version, etc, are handled by code inside the pykg file.

Configuration Header
--------------------

To be valid, a pykg file needs a module-level docstring with, at minimum, a [versions]
section listing the valid versions for this application::

    '''
    [versions]
    6.0v2 =
    6.0v1 =
    5.2v3 =
    5.2v1 =
    5.1v6 =
    5.1v4 =
    '''

A [main] section is used to set global options, like the default version::

    [main]
    executable-path = Nuke
    version-regex = (\d+)\.(\d+)v(\d+)
    default-version = 6.0v6

Version aliases can also be set in the [aliases] section, and are valid to use
anywhere a version is expected, including as the default-version::

    '''
    [main]
    executable-path = Nuke
    version-regex = (\d+)\.(\d+)v(\d+)
    default-version = 6.0

    [aliases]
    6.0 = 6.0v6
    5.2 = 5.2v3

    [versions]
    6.0v2 =
    6.0v1 =
    5.2v3 =
    5.2v1 =
    5.1v6 =
    5.1v4 =
    '''

Execution Environment
---------------------

Several variables and functions are added to the globals of pykg script before it
is executed.

    env :
        instance of an Environment class, providing attribute-style access to
        environment variables. This should be used to modify the environment
        and NOT ``os.environ``.

    NAME :
        a string containing the package name; considered everything before the
        first dash `-` in the package name.

    VERSION :
        a string containing the current version being set; considered everything
        after the first dash `-` in the package name.

    VERSION_PARTS :
        a tuple of version parts if the version string was
        successfully parsed by the `version-regex` config variable, if set;
        otherwise, None

    LOGGER :
        the logger object for this module. normal print statements can also be
        used, but the logger provides log levels (error, warn, info, debug) and
        can also be configured to log to a file.

    setpkg :
        function for setting a sub-package dependency.

    platform module :
        the contents of the builtin `platform` module
        (equivalent of `from platform import *`)

    setpkgutil module :
        contents of `setpkgutil` module, if it exists. this module can be used
        to easily provide utility functions for use within the pykg file. keep
        in mind that the setpkgutil module must be on the PYTHONPATH before
        it can be used.
"""

# TODO:
# colorized output
# collect external variables expanded within a package and auto-reload when they change 
# windows: use getpids.exe to get parent id to allow per-process setpkg'ing like on posix
# windows: add --global flag to set environment globally (current behavior)

from __future__ import with_statement
import os
import posixpath
import sys
import pprint
import re
import subprocess
import platform
import cPickle as pickle
import shelve
import tempfile
import shutil
import hashlib
from collections import defaultdict
from ConfigParser import RawConfigParser, ConfigParser, NoSectionError

try:
    from io import BytesIO as StringIO
except:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

ROLLBACK_RE = re.compile('(,|\()([a-zA-Z][a-zA-Z0-9_]*):')
VER_PREFIX = 'SETPKG_VERSION_'
VER_SEP = ','
LOG_LVL_VAR = 'SETPKG_LOG_LEVEL'

import logging
logger = logging.getLogger("setpkg")
logger.setLevel(logging.DEBUG)

## create file handler which logs even debug messages
#fh = logging.FileHandler("/var/tmp/setpkg.log")
#fh.setLevel(logging.INFO)
#fformatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#fh.setFormatter(fformatter)
#logger.addHandler(fh)

sh = logging.StreamHandler()
if LOG_LVL_VAR in os.environ:
    sh.setLevel(getattr(logging, os.environ[LOG_LVL_VAR]))
else:
    sh.setLevel(logging.WARN)
sformatter = logging.Formatter("%(message)s")
sh.setFormatter(sformatter)
logger.addHandler(sh)

class propertycache(object):
    '''Class for creating properties where the value is initially calculated then stored.

    Intended for use as a descriptor, ie:

    class MyClass(object):
        @propertycache
        def aValue(self):
            return calcValue()
    c = MyClass()
    c.aValue

    '''
    def __init__(self, func):
        self.func = func
        self.name = func.__name__
    def __get__(cls, self, type=None):
        result = cls.func(self)
        setattr(self, cls.name, result)
        return result

def _hashfile(filename):
    hasher = hashlib.sha1()
    infile = open(filename, 'rb')
    try:
        hasher.update(infile.read())
        return hasher.hexdigest()
    finally:
        infile.close()

def _getppid():
    if hasattr(os, 'getppid'):
        return str(os.getppid())
    return 'NULL'

#------------------------------------------------
# Shell Classes
#------------------------------------------------

class Shell(object):
    def prefix(self):
        '''
        Abstract base class representing a system shell.
        '''
        return ''
    def setenv(self, key, value):
        raise NotImplementedError
    def unsetenv(self, key):
        raise NotImplementedError
    def alias(self, key, value):
        raise NotImplementedError

class Bash(Shell):
    def setenv(self, key, value):
        return "export %s=%s;" % ( key, value )
    def unsetenv(self, key):
        return "unset %s;" % ( key, )
    def alias(self, key, value):
        return "alias %s='%s';" % ( key, value)

class Tsch(Shell):
    def setenv(self, key, value):
        return "setenv %s %s;" % ( key, value )
    def unsetenv(self, key):
        return "unsetenv %s;" % ( key, )
    def alias(self, key, value):
        return "alias %s '%s';" % ( key, value)

class WinShell(Shell):
    def __init__(self, set_global=False):
        self.set_global = set_global
    def prefix(self):
        # Add this directory onto the path to make sure setenv is available
        return 'set PATH=%s;%%PATH%%' % THIS_DIR
    def setenv(self, key, value):
        value = value.replace('/', '\\\\')
        # exclamation marks allow delayed expansion
        quotedValue = subprocess.list2cmdline([value])
        # Will add environment variables to user environment variables -
        # HKCU\\Environment
        # ...but not to process environment variables
#        return 'setx %s "%s"\n' % ( key, value )

        # Will TRY to add environment variables to volatile environment variables -
        # HKCU\\Volatile Environment
        # ...but other programs won't 'notice' the registry change
        # Will also add to process env. vars
#        return ('REG ADD "HKCU\\Volatile Environment" /v %s /t REG_SZ /d %s /f\n' % ( key, quotedValue )  +
#                'set "%s=%s"\n' % ( key, value ))

        # Will add to volatile environment variables -
        # HKCU\\Volatile Environment
        # ...and newly launched programs will detect this
        # Will also add to process env. vars
        if self.set_global:
            cmd = 'setenv -v %s %s\n' % (key, quotedValue)
        else:
            cmd = ''
        cmd += 'set %s=%s\n' % (key, value)
        return cmd

    def unsetenv(self, key):
        # env vars are not cleared until restart!
        if self.set_global:
            cmd = 'setenv -v %s -delete\n' % (key,)
        else:
            cmd = ''
        cmd += 'set %s=\n' % (key,)
        return cmd

shells = { 'bash' : Bash,
           'tcsh' : Tsch,
           'DOS' : WinShell}

def get_shell(shell_name):
    return shells[os.path.basename(shell_name)]()

#------------------------------------------------
# Environment Classes
#------------------------------------------------


def _expand(value, strip_quotes=False):
    # use posixpath because setpkg expects posix-style paths and variable expansion
    # (on windows: os.path.expandvars will not expand $FOO-x64)
    expanded = os.path.normpath(os.path.expanduser(posixpath.expandvars(value)))
    if strip_quotes:
        expanded = expanded.strip('"')
    return expanded

def _split(value):
    return value.split(os.pathsep)

def _join(values):
    return os.pathsep.join(values)

def _nativepath(path):
    return os.path.join(path.split('/'))

def prependenv(name, value, expand=True, no_dupes=False):
    if expand:
        value = _expand(value, strip_quotes=True)

    if name not in os.environ:
        os.environ[name] = value
    else:
        current_value = os.environ[name]
        parts = _split(current_value)
        if no_dupes:
            expanded_parts = [_expand(x) for x in parts]
            if value not in expanded_parts:
                parts.insert(0, value)
                new_value = _join(parts)
                os.environ[name] = new_value
        else:
            parts.insert(0, value)
            new_value = _join(parts)
            os.environ[name] = new_value
    #print "prepend", name, value
    return value

def prependenvs(name, value):
    '''
    like prependenv, but in addition to setting single values, it also allows
    value to be a separated list of values (foo:bar) or a python list
    '''
    if isinstance(value, (list, tuple)):
        parts = value
    else:
        parts = _split(value)
    if len(parts) > 1:
        # traverse in reverse order, so precedence given is maintained
        for part in reversed(parts):
            prependenv(name, part)
    else:
        prependenv(name, value)
    return value

def setenv(name, value, expand=True):
    if expand:
        value = _expand(value, strip_quotes=True)
    os.environ[name] = value
    #print "set", name, value
    return value

def popenv(name, value, expand=True):
    if expand:
        value = _expand(value, strip_quotes=True)

    try:
        current_value = os.environ[name]
    except KeyError:
        return
    else:
        parts = _split(current_value)
        try:
            index = parts.index(value)
        except ValueError:
            return
        else:
            if len(parts) == 1:
                del os.environ[name]
            else:
                parts.pop(index)
                os.environ[name] = _join(parts)
    #print "popenv", name, value
    return value

class Environment(object):
    '''
    provides attribute-style access to an environment dictionary.

    combined with EnvironmentVariable class, tracks changes to the environment
    '''
#    def __init__(self, environ=None):
#        self.__dict__['environ'] = environ if environ is not None else os.environ
#
#    def __getattr__(self, attr):
#        return EnvironmentVariable(attr, self.environ)

    def __init__(self):
        self.__dict__['_environ'] = defaultdict(list)

    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            try:
                self.__dict__[attr]
            except KeyError:
                raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, attr))
        return EnvironmentVariable(attr, self.__dict__['_environ'])

    def __setattr__(self, attr, value):
        if isinstance(value, EnvironmentVariable):
            if value.name == attr:
                # makes no sense to set ourselves. most likely a result of:
                # env.VAR += value
                return
            value = value.value()
        else:
            value = str(value)
        self.__dict__['_environ'][attr] = [setenv(attr, value)]

    def __str__(self):
        return pprint.pformat(dict(os.environ))

class EnvironmentVariable(object):
    '''
    class representing an environment variable

    combined with Environment class, tracks changes to the environment
    '''

    def __init__(self, name, environ):
        self._name = name
        self._environ = environ

    def __str__(self):
        return '%s = %s' % (self._name, self.value())

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._name)

    def __nonzero__(self):
        return bool(self.value())

    @property
    def name(self):
        return self._name

    def prepend(self, value):
        if isinstance(value, EnvironmentVariable):
            value = value.value()
        expanded_value = prependenv(self._name, value)
        # track changes
        self._environ[self._name].insert(0, expanded_value)

        # update_pypath
        if self.name == 'PYTHONPATH':
            sys.path.insert(0, expanded_value)
        return expanded_value

    def set(self, value):
        if isinstance(value, EnvironmentVariable):
            value = value.value()
        expanded_value = setenv(self._name, value)
        # track changes
        self._environ[self._name] = [expanded_value]
        return expanded_value

    def setdefault(self, value):
        '''
        set value if the variable does not yet exist
        '''
        if self:
            return self.value()
        else:
            return self.set(value)

    def __add__(self, value):
        '''
        append `value` to this variable's value.

        returns a string
        '''
        if isinstance(value, EnvironmentVariable):
            value = value.value()
        return self.value() + value

    def __iadd__(self, value):
        self.prepend(value)
        return self

    def __eq__(self, value):
        if isinstance(value, EnvironmentVariable):
            value = value.value()
        return self.value() == value

    def __div__(self, value):
        return os.path.join(self.value(), *value.split('/'))

    def value(self):
        return os.environ.get(self._name, None)

    def split(self):
        return _split(self.value())

#------------------------------------------------
# Package Files
#------------------------------------------------

class PackageError(ValueError):
    def __init__(self, package, detail):
        self.package = package
        self.detail = detail
    def __str__(self):
        return '%s: %s' % (self.package, self.detail)

class InvalidPackageVersion(PackageError):
    def __init__(self, package, bad_version, detail):
        self.package = package
        self.bad_version = bad_version
        self.detail = detail
    def __str__(self):
        return '%s: invalid version %s: %s' % (self.package, self.bad_version, self.detail)

class PackageExecutionError(PackageError):
    def __str__(self):
        return 'error during execution of %s.pykg file: %s' % (self.package, self.detail)


def _shortname(package):
    return package.split('-', 1)[0]

def _longname(name, version):
    assert version is not None
    return '%s-%s' % (name, version)

def _splitname(package):
    parts = package.split('-', 1)
    version = None if len(parts) == 1 else parts[1]
    return parts[0], version

def _parse_header(file):
    header = []
    started = False
    with open(file, 'r') as f:
        for line in f:
            line = line.strip()
            if started:
                if line.endswith("'''") or line.endswith('"""'):
                    header.append(line[:-3])
                    break
                else:
                    header.append(line)
            else:
                if line.startswith("'''") or line.startswith('"""'):
                    started = True
                    header.append(line[3:])

                elif line and not line.startswith('#'):
                    # only empty or comment lines are allowed before the header docstring.
                    # this keeps us from parsing an entire package file only
                    # to discover the header was omitted
                    break
    return header

def _pkgpaths():
    if 'SETPKG_PATH' not in os.environ:
        raise ValueError('SETPKG_PATH environment variable not set!')
    return _split(os.environ['SETPKG_PATH'])

def find_package_file(name):
    '''
    given an unversioned package name, search SETPKG_PATH for the .pykg file

    :param name: a versioned or unversioned package name
    '''
    for path in _pkgpaths():
        file = os.path.join(_expand(path), (name + '.pykg'))
        if os.path.exists(file):
            return file
    raise PackageError(name, 'unknown package')

def walk_package_files():
    for path in _pkgpaths():
        for f in sorted(os.listdir(path)):
            if f.endswith('.pykg'):
                yield os.path.join(path, f)

def list_package_choices(package=None, versions=True, aliases=False):
    '''
    list available packages in NAME-VERSION format.

    :param package: name of package to list versions for.  if None, lists
        all available packages and versions

    '''
    packages = []
    if package:
        package_files = [find_package_file(package)]
    else:
        package_files = sorted(walk_package_files())

    if not versions:
        return [ os.path.splitext(os.path.basename(file))[0] for file in package_files]

    for package_file in package_files:
        try:
            pkg = Package(package_file)
            for version in pkg.versions:
                packages.append('%s-%s' % (pkg.name, version))
            if aliases:
                for alias in sorted(pkg.aliases):
                    packages.append('%s-%s' % (pkg.name, alias))
        except PackageError, err:
            pass
            #logger.error(str(err))
    return packages

def get_package(name):
    '''
    find a package on SETPKG_PATH and return a Package class.

    :param name: a versioned or unversioned package name
    '''
    shortname, version = _splitname(name)
    return Package(find_package_file(shortname), version)

def _current_data(name):
    '''
    return the version and pykg file hash for the given pkg
    '''
    shortname = _shortname(name)
    try:
        data = os.environ[VER_PREFIX + shortname].split(VER_SEP)
    except KeyError:
        return (None, None)
    else:
        if len(data) == 1:
            return (data[0], None)
        elif len(data) == 2:
            return tuple(data)
        else:
            raise PackageError(shortname, 'corrupted version data')

def current_version(name):
    '''
    get the currently set version for the given pkg, or None if it is not set

    :param name: a versioned or unversioned package name
    '''
    return _current_data(name)[0]

def current_versions():
    '''
    return a dictionary of shortname to version for all active packages
    '''
    return dict([(k[len(VER_PREFIX):], os.environ[k].split(VER_SEP)[0]) \
                     for k in os.environ if k.startswith(VER_PREFIX)])

class FakePackage(object):
    '''
    A package that does not exist on disk
    '''
    def __init__(self, name, version):
        self.name = name,
        self.version = version
        self.versions = [self.version]
        self._environ = Environment()
    @property
    def environ(self):
        return dict(self._environ.__dict__['_environ'])

    @propertycache
    def hash(self):
        return '%s-%s' % (self.name, sel.version)

class Package(object):
    '''
    Class representing a .pykg package file on disk.
    '''
    # allowed characters: letters, numbers, period, dash, underscore
    VERSION_RE = re.compile('[a-zA-Z0-9\.\-_]+$')
    def __init__(self, file, version=None):
        '''
        instantiate a package from a package file.

        :param version: if version is not provided, the default version is
            automatically determined from the `default-version` configuration
            variable in the package header. If that is not set and the lists of the
            `versions` configuration variable is exactly one, that value is used,
            otherwise an error is raised.
        '''
        self.file = file
        self.name = os.path.splitext(os.path.basename(file))[0]
        self._version = version
        self._parent = None
        self._dependencies = []
        self._dependents = []
        self._environ = Environment()

    def __eq__(self, other):
        # use file instead?
        return (self.name, self.version) == (other.name, other.version)

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.file, self.version)

    @property
    def explicit_version(self):
        '''
        True if this package explicitly requested a particular version or
        False if it accepted the default version.
        '''
        return bool(self._version)

    @propertycache
    def version(self):
        version = self._version
        if not version:
            if self.config.has_option('main', 'default-version'):
                version = self.config.get('main', 'default-version')
            elif len(self.versions) == 1:
                version = self.versions[0]
            else:
                raise PackageError(self.name, "no 'default-version' specified in package header ([main] section)")

        if version not in self.versions:
            try:
                # expand aliases
                version = self.aliases[version]
            except KeyError:
                if not self.explicit_version:
                    version = '%s (default)' % version
                raise InvalidPackageVersion(self.name, version, '(valid choices are %s)' % ', '.join(self.versions))
        return version

    @propertycache
    def config(self):
        '''
        read the header of a package file into a python ConfigParser
        '''
        lines = _parse_header(self.file)
        text = '\n'.join(lines)
        config = ConfigParser()
        config.readfp(StringIO(text))
#        if not config.has_section('main'):
#            raise PackageError(self.name, 'no [main] section in package header')
        return config

    @propertycache
    def versions(self):
        '''
        list of versions taken from the `versions` config option in the `main` section
        '''
        #versions = [v.strip() for v in self.config.get('main', 'versions').split(',')]
        try:
            versions = [k.strip() for k, v in self.config.items('versions')]
        except NoSectionError:
            raise PackageError(self.name, 'no [versions] section in package header')
        valid = []
        for version in versions:
            if self.VERSION_RE.match(version):
                valid.append(version)
            else:
                logger.warn( "version in package file is invalidly formatted: %r\n" % version )
        if not valid:
            raise PackageError(self.name, "No valid versions were found")
        return valid

    @propertycache
    def aliases(self):
        '''
        A dictionary of {alias : version}. Aliases are recursively expanded.
        '''
        if self.config.has_section('aliases'):
            aliases = dict([(k,v) for k,v in self.config.items('aliases')])

            def expand_alias(alias, value):
                if value is None:
                    return
                elif value in self.versions:
                    return value
                else:
                    try:
                        value = aliases[value]
                    except KeyError:
                        # it's not in versions and it's not in aliases. it's invalid
                        return None
                    else:
                        return expand_alias(alias, value)
            # expand aliases
            for alias, value in aliases.items():
                result = expand_alias(alias, value)
                if result is None:
                    aliases.pop(alias)
                else:
                    aliases[alias] = result
            return aliases
        return {}

    @propertycache
    def version_parts(self):
        '''
        A tuple of version components determined by `version-regex` configuration
        variable. If `version-regex` is not set, returns None.

        For example, for a package with a configuration like the following::

        [main]
        versions = 1.5.1, 1.4.2, 1.3.0
        version-regex = (\d+)\.(\d+)\.(\d+)
        default-version = 1.5.1

        the Package.version_parts would contain (1,5,1)
        '''
        if self.config.has_option('main', 'version-regex'):
            reg = self.config.get('main', 'version-regex')+'$'
            try:
                return re.match(reg, self.version).groups()
            except AttributeError:
                logger.warn('could not split version using version-regex %r' % reg)

    @propertycache
    def executable(self):
        '''
        read and expand executable-path configuration variable. if it does not exist,
        simply return the short name of the package
        '''
        if self.config.has_option('main', 'executable-path'):
            return self.config.get('main', 'executable-path')
        else:
            return self.name

    @propertycache
    def hash(self):
        return _hashfile(self.file)

    @property
    def fullname(self):
        return self.name + '-' + self.version

    @property
    def parent(self):
        return self._parent

    @property
    def parents(self):
        if self._parent:
            yield self._parent
            for parent in self._parent.parents:
                yield parent

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def dependents(self):
        return self._dependents

#    def walk_dependencies(self):
#        for child in self._dependencies:
#            yield child
#            for gchild in child.walk_dependencies():
#                yield gchild

    def depends_on(self, package):
        self._dependencies.append(package)
        package._dependents.append(self)

    @property
    def environ(self):
        return dict(self._environ.__dict__['_environ'])

#------------------------------------------------
# Session
#------------------------------------------------

class Session():
    '''
    A persistent session that manages the adding and removing of packages.

    The session contains a python shelf that pickles the Package classes of the
    active packages.

    When adding a package, if the requested version of the package has not yet
    been set, the .pykg file is executed in a special python environment created
    by the session.

    the environment includes these python objects:

        - env: instance of an Environment class
        - VERSION: a string containing the current version being set
        - NAME: a string containing the package name
        - VERSION_PARTS: a tuple of version parts if the version string was
            successfully parsed by `version-regex`; otherwise, None
        - LOGGER: the logger object for this module
        - setpkg: function for setting a sub-package
        - contents of the builtin `platform` module (equivalent of `from platform import *`)
        - contents of `setpkgutil` module, if it exists
    '''
    def __init__(self, pid=None, protocol=2):
        self._added = []
        self._removed = []
        self.out = sys.stderr
        self.pid = pid if pid else _getppid()
        self.filename = None

    def __enter__(self):
        #logger.debug( "new session %s" % self.filename )
        return self

    def __exit__(self, type, value, traceback):
        #logger.debug('session closed')
        self.close()

    def _open_shelf(self, protocol=None, writeback=False, pid=None):
        """
        """
        SESSION_PREFIX = 'setpkg_session_'
        if 'SETPKG_SESSION' in os.environ:
            filename = os.environ['SETPKG_SESSION']
            # see if our pid differs from the existing
            old_pid = filename.rsplit('_')[-1]
            if pid != old_pid:
                # make a unique copy for us
                old_filename = filename
                filename = os.path.join(tempfile.gettempdir(), (SESSION_PREFIX + pid))
                logger.info('copying cache from %s to %s' % (old_filename, filename))
                # depending on the underlying database type used by shelve,
                # the file may actually be several files
                try:
                    shutil.copy(old_filename, filename)
                except:
                    for suffix in ['.bak', '.dat', '.dir']:
                        shutil.copy(old_filename + suffix, filename + suffix)
                pkg = FakePackage('setpkg', version='2.0')
                pkg._environ.SETPKG_SESSION.set(filename)
                self._added.append(pkg)

            # read an existing shelf
            flag = 'w'
            logger.info( "opening existing session %s" % filename )
        else:
            filename = os.path.join(tempfile.gettempdir(), (SESSION_PREFIX + pid))

            # create a new shelf
            flag = 'n'
            logger.info( "opening new session %s" % filename )

            pkg = FakePackage('setpkg', version='2.0')
            pkg._environ.SETPKG_SESSION.set(filename)
            self._added.append(pkg)

        self.filename = filename
        return shelve.DbfilenameShelf(filename, flag, protocol, writeback)

    @propertycache
    def shelf(self):
        return self._open_shelf(pid=self.pid)

    def _status(self, action, package, symbol=' ', depth=0):
        #prefix = '   ' * depth + '[%s]  ' % symbol
        prefix = '[%s]  ' % symbol + ('  ' * depth)
        self.out.write(('%s:' % action).ljust(12) + prefix + '%s\n' % (package,))
        logger.info('%s: %s' % (package, action))

    def _exec_package(self, package, depth=0):

        def filter_local(module):
            return [(k,v) for k,v in module.__dict__.iteritems() if not k.startswith('_')]
        g = {}
        # environment
        g['env'] = package._environ

        # version
        g['VERSION'] = package.version
        g['NAME'] = package.name

        version_parts = package.version_parts
        g['VERSION_PARTS'] = version_parts

        g['LOGGER'] = logger

        # setpkg command
        def setpkg(subname):
            self.add_package(subname, parent=package, depth=depth+1)
        g['setpkg'] = setpkg

        # platform utilities
        import platform
        g.update(filter_local(platform))

        try:
            import setpkgutil
            for protected in g.keys():
                assert protected not in setpkgutil.__dict__, \
                    "setpkgutil contains object with protected name: %s" % protected
            g.update(filter_local(setpkgutil))
        except ImportError:
            pass
        #logger.debug('%s: execfile %r' % (package.fullname, package.file))
#        try:
            # add the current version to the environment tracked by this pacakge
        setattr(g['env'], '%s%s' % (VER_PREFIX, package.name), '%s%s%s' % (package.version, VER_SEP, package.hash))
        execfile(package.file, g)
#        except Exception, err:
#            # TODO: add line and context info for last frame
#            import traceback
#            traceback.print_exc(file=self.out)
#            raise PackageExecutionError(package.name, str(err))
        #logger.debug('%s: execfile complete' % package.fullname)


    def add_package(self, name, parent=None, force=False, depth=0):
        package = get_package(name)
        shortname = package.name

        curr_version, hash = _current_data(shortname)
        if force:
            self.remove_package(shortname, depth=depth+1)
        # check if we've already been set:
        elif curr_version is not None:
            if hash != package.hash:
                self.remove_package(shortname, recurse=True, depth=depth)
            elif not package.explicit_version or curr_version == package.version:
                # a package of this type is already active and
                # A) the version requested is the same OR
                # B) a specific version was not requested
                self._status('skipping', name, ' ', depth)
                if parent and package not in parent.dependencies:
                    parent.depends_on(package)
                    if package.name not in self.shelf:
                        # We need to figure out in which situations this happens...
                        # put in an obnoxious warning until we do
                        logger.debug("=" * 60)
                        logger.debug("Package %s not in shelf, but has version %s..." % (name, curr_version))
                        logger.debug("Parent: %s" % parent)
                        logger.debug("=" * 60)
                        self.shelf[shortname] = package
                return
            else:
                self.remove_package(shortname, depth=depth)

        if parent:
            parent.depends_on(package)

        self._status('adding', package.fullname, '+', depth)
        self._added.append(package)

        self._exec_package(package, depth=depth)

        del package.versions
        del package.config
        self.shelf[package.name] = package
        return package

    def remove_package(self, name, recurse=False, depth=0):
        shortname, version = _splitname(name)
        curr_version = current_version(shortname)
        if curr_version is None:
            raise PackageError(shortname, "package is not currently set")
        package = self.shelf[shortname]
        if version:
            if package.version != version:
                raise InvalidPackageVersion(package, version,
                    "cannot be removed because it is not currently set (active version is %s)" % (package.version,))
        for var, values in package.environ.iteritems():

            for value in values:
                popenv(var, value, expand=False)

        #depth = len(list(package.parents))
        self._status('removing', package.fullname, '-', depth)
        del self.shelf[shortname]
        # clear package --> version cache
        self._removed.append(package)

        if recurse:
            for sub in package.dependencies:
                if sub.dependents == [package]:
                    # current package is only dependency
                    if isinstance(sub, Package):
                        sub = sub.fullname
                    self.remove_package(sub, recurse, depth+1)
                else:
                    logger.warn('not removing %s because it has other dependents' % sub.fullname)
        else:
            for parent in package.dependents:
                if package.explicit_version:
                    logger.warn('WARNING: %s package requires removed package %s' % (parent.fullname, package.fullname))

    @property
    def added(self):
        return self._added

    @property
    def removed(self):
        return self._removed

def setpkg(packages, force=False, update_pypath=False, pid=None):
    """
    :param update_pythonpath: set to True if changes to PYTHONPATH should be
        reflected in sys.path
    :param force: set to True if package should be re-run (unloaded, then
        loaded again) if already loaded
    """
    logger.debug('setpkg %s' % ([force, update_pypath, pid, sys.executable]))
    if isinstance(packages, basestring):
        packages = [packages]
    session = Session(pid=pid)
    for name in packages:
        session.add_package(name, force=force)

    return session.added, session.removed

def unsetpkg(packages, recurse=False, update_pypath=False, pid=None):
    """
    :param update_pythonpath: set to True if changes to PYTHONPATH should be
        reflected in sys.path
    :param force: set to True if package should be re-run (unloaded, then
        loaded again) if already loaded
    """
    if isinstance(packages, basestring):
        packages = [packages]
    session = Session(pid=pid)
    for name in packages:
        session.remove_package(name, recurse=recurse)

    return session.removed

def list_active_packages(package=None, pid=None):
    versions = current_versions()
    if package:
        if package in versions:
            return ['%s-%s' % (package, versions[package])]
        else:
            print "package %s is not currently active" % package
    else:
        return ['%s-%s' % (pkg, versions[pkg]) for pkg in sorted(versions.keys())]
