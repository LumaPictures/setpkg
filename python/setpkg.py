"""
An environment variable management system written in python.  The system is
based around .pykg files: python scripts executed in a special environment and
containing python ini-style configuration headers.

==================================
pykg files
==================================

Typically, a single .pykg file is written for each application to be managed,
and placed on the SETPKG_PATH. When adding a package using the setpkg module or
command line tool, if the requested version of the package has not yet already
been set, the .pykg file is executed. Differences per OS, architecture, application
version, etc, are handled by code inside the pykg file.

----------------------------------
Configuration Header Sections
----------------------------------

main
====

Used to set global options

**executable-path**
    name of the executable for the package, used by `pkg run`

**version-regex**
    validates the version and splits it into components provided as VERSION_PARTS (see below)

**default-version**
    the version used when no version is specified

example main section::

    [main]
    executable-path = Nuke
    version-regex = (\d+)\.(\d+)v(\d+)
    default-version = 6.0v6

requires
========

Requirements are loaded before this current package is loaded. 

If a specific version of a package is given as a requirement
and a different version of the package is already loaded, it (and all of its
dependencies) will be reloaded with the new version.  If no version is specified,
and the package is already loaded, it will be used as is, otherwise the default
version will be loaded.

The left side of each requires statement is a unix-style glob pattern for specifying
which versions of the current package to associate with the requirement on the
right side::

    [requires]
    6.* = python-2.5
    5.* = python-2.5

subs
====

Subpackages are loaded after the current package is loaded.

The left side of each requires statement is a unix-style glob pattern for specifying
which versions of the current package to associate with the requirement on the
right side::

    [subs]
    * = djv

versions
========

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

aliases
=======

Alternate names for versions. These are valid to use
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

----------------------------------
Package Body
----------------------------------

The body of the pykg is regular python executed in a specially prepared environment.

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

    platform module :
        the contents of the builtin `platform` module
        (equivalent of `from platform import *`)

    setpkgutil module :
        contents of `setpkgutil` module, if it exists. this module can be used
        to easily provide utility functions for use within the pykg file. keep
        in mind that the setpkgutil module must be on the PYTHONPATH before
        it can be used.
        
==================================
Commandline Tools
==================================

The core command is called `pkg`, which has several sub-commands, notably `set`,
`unset`, `ls`, `run`, and `info` (call `pkg -h` for details)

here's a simple example, using the Nuke package file outlined above::

    $ setpkg nuke             
    adding:     [+]  nuke-6.1v2                                          
    adding:     [+]    python-2.5                                        
    adding:     [+]      lumaTools-1.0                                   
    adding:     [+]      pyexternal-1.0                                  
    adding:     [+]        pymel-1.0                                     
    adding:     [+]    djv-0.8.3.p2                                      
    $ setpkg nuke-6.0v6       
    switching:  [+]  nuke-6.1v2 --> 6.0v6                                
    $ unsetpkg nuke
    removing:   [-]  nuke-6.0v6
    $ setpkg nuke-6.0v6
    adding:     [+]  nuke-6.0v6
    $ pkg info nuke
    name:               nuke
    executable:         Nuke
    versions:           5.1v1, 5.1v2, 5.1v3, 5.1v4, 5.1v6, 5.2v1, 5.2v3, 6.0v1, 6.0v2, 6.0v3, 6.0v6, 6.1v1, 6.1v2, 6.1v3
    subpackages:        djv
    dependencies:       python-2.5
    dependents:
    active version:     6.0v6
    run commands:       [command]                     [action]
                        nuke5                         runpkg nuke-5.2v3
                        nuke6                         runpkg nuke-6.0v6
    package aliases:    [alias]                       [package]
                        5.2                           5.2v3
                        6.0                           6.0v6
                        6.1                           6.1v2
    variables:          [variable]                    [values]
                        NUKE_APP                      /usr/local/Nuke6.0v6
                        NUKE_GIZMO_PATH               /lumalocal/dev/chad/nuke/gizmos
                        NUKE_PATH                     /Volumes/luma/_globalSoft/nuke/icons
                                                      /lumalocal/dev/chad/nuke/gizmos
                                                      /lumalocal/dev/chad/nuke/python
                                                      /lumalocal/dev/chad/nuke/plugins/6.0/Linux-x86_64
                                                      /lumalocal/dev/chad/nuke/python
                        NUKE_PYTHON_PATH              /lumalocal/dev/chad/nuke/python
                        NUKE_VER                      6.0v6
                        NUKE_VERSION_MAJOR            6
                        NUKE_VERSION_MINOR            0
                        NUKE_VERSION_REVISION         6
                        OFX_PLUGIN_PATH               /Volumes/luma/_globalSoft/nuke/ofx_plugins/Linux-x86_64
                        PATH                          /lumalocal/dev/chad/nuke/bin
                                                      /usr/local/Nuke6.0v6
                        PYTHONPATH                    /lumalocal/dev/chad/nuke/python
    $ unsetpkg nuke
    removing:   [-]  nuke-6.0v6

==================================
Installation
==================================

----------------------------------
OSX/Linux
----------------------------------

Bash
====

In one of you system startup scripts (/etc/profile, ~/.bashrc, ~/.bash_profile, etc) add the
following lines:

    export SETPKG_ROOT=/path/to/setpkg
    source $SETPKG_ROOT/scripts/setpkg.sh

Tcsh
====

In one of you system startup scripts (/etc/csh.login, /etc/csh.cshrc, ~/.tcshrc, etc) add the
following lines:

    setenv SETPKG_ROOT /path/to/setpkg
    source $SETPKG_ROOT/scripts/setpkg.csh

"""

# TODO:
# colorized output (could be added to the logger?)
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
import inspect
import fnmatch
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
REQ_PREFIX = 'SETPKG_REQUIRES_'
META_SEP = ','
PKG_SEP = '-'
LOG_LVL_VAR = 'SETPKG_LOG_LEVEL'

import logging
logger = logging.getLogger("setpkg")
logger.setLevel(logging.INFO)

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

#===============================================================================
# Utilities
#===============================================================================

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

# This is actually just copied from pymel.util.shell, but I didn't want
# external dependencies...
def executableOutput(exeAndArgs, convertNewlines=True, stripTrailingNewline=True,
                     returnCode=False, input=None, **kwargs):
    """Will return the text output of running the given executable with the given arguments.

    This is just a convenience wrapper for subprocess.Popen, so the exeAndArgs argment
    should have the same format as the first argument to Popen: ie, either a single string
    giving the executable, or a list where the first element is the executable and the rest
    are arguments.

    :Parameters:
        convertNewlines : bool
            if True, will replace os-specific newlines (ie, \\r\\n on Windows) with
            the standard \\n newline

        stripTrailingNewline : bool
            if True, and the output from the executable contains a final newline,
            it is removed from the return value
            Note: the newline that is stripped is the one given by os.linesep, not \\n
            
        returnCode : bool
            if True, the return will be a tuple, (output, returnCode)
            
        input : string
            if non-none, a string that will be sent to the stdin of the executable

    kwargs are passed onto subprocess.Popen

    Note that if the keyword arg 'stdout' is supplied (and is something other than subprocess.PIPE),
    then the return will be empty - you must check the file object supplied as the stdout yourself.

    Also, 'stderr' is given the default value of subprocess.STDOUT, so that the return will be
    the combined output of stdout and stderr.

    Finally, since maya's python build doesn't support universal_newlines, this is always set to False -
    however, set convertNewlines to True for an equivalent result."""

    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('stderr', subprocess.STDOUT)
    
    if input:
        kwargs.setdefault('stdin', subprocess.PIPE)

    cmdProcess = subprocess.Popen(exeAndArgs, **kwargs)
    cmdOutput = cmdProcess.communicate(input=input)[0]

    if stripTrailingNewline and cmdOutput.endswith(os.linesep):
        cmdOutput = cmdOutput[:-len(os.linesep)]

    if convertNewlines:
        cmdOutput = cmdOutput.replace(os.linesep, '\n')
    if returnCode:
        return cmdOutput, cmdProcess.returncode
    return cmdOutput

#------------------------------------------------
# Shell Classes
#------------------------------------------------

class Shell(object):
    def __init__(self, **kwargs):
        pass

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

class Tcsh(Shell):
    def setenv(self, key, value):
        return "setenv %s %s;" % ( key, value )
    def unsetenv(self, key):
        return "unsetenv %s;" % ( key, )
    def alias(self, key, value):
        return "alias %s '%s';" % ( key, value)

class WinShell(Shell):
    def __init__(self, set_global=False):
        self.set_global = set_global
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
           'sh'   : Bash,
           'tcsh' : Tcsh,
           'csh'  : Tcsh,
           '-csh' : Tcsh, # For some reason, inside of 'screen', ps -o args reports -csh...
           'DOS' : WinShell}

def get_shell_name():
    command = executableOutput(['ps', '-o', 'args=', '-p', str(os.getppid())]).strip()
    return command.split()[0]

def get_shell_class(shell_name):
    if shell_name is None:
        shell_name = get_shell_name()
    return shells[os.path.basename(shell_name)]

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
            if expand:
                expanded_parts = [_expand(x) for x in parts]
            else:
                expanded_parts = parts
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

def appendenv(name, value, expand=True, no_dupes=False):
    if expand:
        value = _expand(value, strip_quotes=True)

    if name not in os.environ:
        os.environ[name] = value
    else:
        current_value = os.environ[name]
        parts = _split(current_value)
        if no_dupes:
            if expand:
                expanded_parts = [_expand(x) for x in parts]
            else:
                expanded_parts = parts
            if value not in expanded_parts:
                parts.append(value)
                new_value = _join(parts)
                os.environ[name] = new_value
        else:
            parts.append(value)
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
    # traverse in reverse order, so precedence given is maintained
    for part in reversed(parts):
        prependenv(name, part)
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

    # There's some code duplication between Environment.__setattr__ and
    # EnvironmentVariable.set... going to leave it as is, assuming it's
    # duplicated for speed reasons... just remember to edit both places
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
        
    def __contains__(self, attr):
        return attr in os.environ

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

    def prepend(self, value, **kwargs):
        if isinstance(value, EnvironmentVariable):
            value = value.value()
        expanded_value = prependenv(self._name, value, **kwargs)
        # track changes
        self._environ[self._name].insert(0, expanded_value)

        # update_pypath
        if self.name == 'PYTHONPATH':
            sys.path.insert(0, expanded_value)
        return expanded_value

    def append(self, value, **kwargs):
        if isinstance(value, EnvironmentVariable):
            value = value.value()
        expanded_value = appendenv(self._name, value, **kwargs)
        # track changes
        self._environ[self._name].append(expanded_value)

        # update_pypath
        if self.name == 'PYTHONPATH':
            sys.path.append(expanded_value)
        return expanded_value

    # There's some code duplication between Environment.__setattr__ and
    # EnvironmentVariable.set... going to leave it as is, assuming it's
    # duplicated for speed reasons... just remember to edit both places
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
        # FIXME: value could be None.  should we return empty list or raise an error?
        value = self.value()
        if value is not None:
            return _split(value)
        else:
            return []

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


def _shortname(package_name):
    return package_name.split(PKG_SEP, 1)[0]

def _longname(name, version):
    assert version is not None
    return name + PKG_SEP + version

def _splitname(package_name):
    parts = package_name.split(PKG_SEP, 1)
    version = None if len(parts) == 1 else parts[1]
    return parts[0], version

def _joinname(name, version):
    return name + PKG_SEP + version

def _hasversion(package_name):
    return len(package_name.split(PKG_SEP, 1)) == 2

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
                packages.append(_joinname(pkg.name, version))
            if aliases:
                for alias in sorted(pkg.aliases):
                    packages.append(_joinname(pkg.name, alias))
        except PackageError, err:
            logger.debug(str(err))
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
        data = os.environ[VER_PREFIX + shortname].split(META_SEP)
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
    return dict([(k[len(VER_PREFIX):], os.environ[k].split(META_SEP)[0]) \
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
        return _joinname(self.name, self.version)

class BasePackage(object):

    @property
    def fullname(self):
        return _joinname(self.name, self.version)

    @property
    def explicit_version(self):
        '''
        True if this package explicitly requested a particular version or
        False if it accepted the default version.
        '''
        return bool(self._version)

    def get_dependencies(self):
        var = 'SETPKG_DEPENDENCIES_%s' % self.name
        val = os.environ.get(var, None)
        if val:
            return [PackageInterface(pkg) for pkg in _split(val)]
        else:
            return []

    def get_dependents(self):
        '''
        return a list of (dependent, explicit_version)
        
        explicit_version will be True if this dependent specified a version
        of the current package
        '''
        try:
            return [PackageInterface(name) for name in _split(os.environ['SETPKG_DEPENDENTS_%s' % self.name])]
        except KeyError:
            return []

    def walk_dependents(self):
        for dependent in self.get_dependents():
            if not self.requires_explicit_version(dependent.name):
                yield dependent
            for subdepend in dependent.get_dependents():
                yield subdepend

    def get_dependency_versions(self):
        '''
        return a dictionary mapping dependency shortnames to versions. version
        will be None if no version was required
        '''
        try:
            return dict([_splitname(pkg) \
                for pkg in _split(os.environ['SETPKG_DEPENDENCIES_%s' % self.name])])
        except KeyError:
            return {}

    def required_version(self, package):
        return PackageInterface(package).get_dependency_versions()[self.name]

    def is_active(self):
        return VER_PREFIX + self.name in os.environ

    def __eq__(self, other):
        # use file instead?
        return (self.name, self.version) == (other.name, other.version)

class PackageInterface(BasePackage):
    '''
    Represents an active package
    '''
    def __init__(self, name):
        self.origname = name
        self.name, self._version = _splitname(name)
        # TODO: assert version

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.origname)

    @propertycache
    def hash(self):
        try:
            version, hash = os.environ[VER_PREFIX + self.name].split(META_SEP)
        except KeyError:
            # TODO: different error
            raise
        self.version = version
        return hash

    @propertycache
    def version(self):
        try:
            version, hash = os.environ[VER_PREFIX + self.name].split(META_SEP)
        except KeyError:
            # TODO: different error
            raise
        
        if self._version:
            if self._version != version:
                raise InvalidPackageVersion(self.name, self._version, 'active version is %s' % version)
        self.hash = hash
        return version

    def add_dependent(self, package):
        var = 'SETPKG_DEPENDENTS_%s' % self.name
        prependenv(var, package.name)

class Package(BasePackage):
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

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.file, self.version)

    @property
    def origname(self):
        if self.explicit_version:
            return _joinname(self.name, self.version)
        else:
            return self.name

    def _read_packagelist(self, section):
        pkgs = []
        if self.config.has_section(section):
            for glob, pkglist in self.config.items(section):
                if re.compile(fnmatch.translate(glob)).match(self.version):
                    for pkg in pkglist.split(','):
                        pkgs.append(pkg.strip())
        return pkgs
  
    @property
    def fullname(self):
        return _joinname(self.name, self.version)

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
        config = ConfigParser()
        try:
            lines = _parse_header(self.file)
            text = '\n'.join(lines)
            config.readfp(StringIO(text))
    #        if not config.has_section('main'):
    #            raise PackageError(self.name, 'no [main] section in package header')
        except Exception, e:
            try:
                selfStr = str(self)
            except Exception:
                selfStr = '<unknown package>'
            try:
                exceptionMsg = str(e)
            except Exception:
                exceptionMsg = '<unknown error>'
            logger.error('Error reading config for package %s: %s' % (selfStr, exceptionMsg))
            import traceback
            logger.debug(traceback.format_exc())
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
            match = self.VERSION_RE.match(version)
            if match:
                # add a tuple with the version_parts, for sorting
                valid.append( (match.groups(), version) )
            else:
                logger.warn( "version in package file is invalidly formatted: %r\n" % version )
        if not valid:
            raise PackageError(self.name, "No valid versions were found")
        return [version for parts, version in sorted(valid)]

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
    def system_aliases(self):
        '''
        return a list of (alias, packagename) tuples
        '''
        result = []
        if self.config.has_section('system-aliases'):
            for alias_suffix, pkg_version in self.config.items('system-aliases'):
                if not pkg_version:
                    pkg_version = alias_suffix
                result.append((self.name + alias_suffix, 
                               _joinname(self.name, self.aliases.get(pkg_version, pkg_version))))
        return result
                    
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
    def parent(self):
        return self._parent

    @property
    def parents(self):
        if self._parent:
            yield self._parent
            for parent in self._parent.parents:
                yield parent
    
    @propertycache
    def subpackages(self):
        '''
        read subpackages from the pykg [subs] section
        '''
        return self._read_packagelist('subs')

    def get_dependencies(self):
        return [ PackageInterface(pkg) for pkg in self._read_packagelist('requires')]
        
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
                for suffix in ['', '.bak', '.dat', '.dir', '.db']:
                    if os.path.exists(old_filename + suffix):
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
        def subpkg(subname):
            self.add_package(subname, parent=package, depth=depth+1)
        g['setpkg'] = subpkg

        # platform utilities
        import platform
        # filter local and non-functions
        g.update([(k,v) for k,v in platform.__dict__.iteritems() \
                  if not k.startswith('_') and inspect.isfunction(v)])

        try:
            import setpkgutil
            utildict = setpkgutil.__dict__.copy()
            overrides = set(g.keys()).intersection(utildict.keys())
            for o in overrides:
                logger.warn("setpkgutil contains object with protected name %r: ignoring" % o)
                utildict.pop(o)
            # filter local
            g.update([(k,v) for k,v in utildict.iteritems() if not k.startswith('_')])
        except ImportError:
            pass
        #logger.debug('%s: execfile %r' % (package.fullname, package.file))
#        try:
            # add the current version to the environment tracked by this pacakge
        setattr(g['env'], '%s%s' % (VER_PREFIX, package.name), 
                '%s%s%s' % (package.version, META_SEP, package.hash))

        def load(section, prefix, parent):
            pkgs = package._read_packagelist(section)
            for pkg in pkgs:
                self.add_package(pkg, parent=parent, depth=depth+1)
            return pkgs  

        requirements = load('requires', 'DEPENDENCIES', None)

        # add ourself to the dependents of our dependencies (or did i just blow your mind?)
        for pkg in requirements:
            shortname, version = _splitname(pkg)
            var = getattr(g['env'], 'SETPKG_DEPENDENTS_%s' % (shortname,))
            var.append(package.name, expand=False)
        
        # add our direct dependencies, using shortname
        var = getattr(g['env'], 'SETPKG_DEPENDENCIES_%s' % (package.name,))
        values = set(var.split())
        for pkg in requirements:
            if pkg not in values:
                var.append(pkg, expand=False)

        # Execute the file!
#        try:
        execfile(package.file, g)
#        except Exception, err:
#            # TODO: add line and context info for last frame
#            import traceback
#            traceback.print_exc(file=self.out)
#            raise PackageExecutionError(package.name, str(err))
        #logger.debug('%s: execfile complete' % package.fullname)
         
        subpackages = load('subs', 'DEPENDENTS', package)

#        # not necessary:: we can get the list from [subs]
#        # add our subpackages
#        var = getattr(g['env'], 'SETPKG_SUBS_%s' % (package.name,))
#        for pkg in subpackages:
#            var.prepend(pkg, expand=False)

    def add_package(self, name, parent=None, force=False, depth=0):
        package = get_package(name)
        shortname = package.name
        curr = PackageInterface(shortname)
        reloading = False
        if force:
            reloading = True
            self._status('reloading', package.fullname, '+', depth)
            self.remove_package(curr.name, depth=depth+1, reloading=True)
        # check if we've already been set:
        elif curr.is_active():
            if curr.hash != package.hash:
                reloading = True
                self._status('refreshing', package.fullname, '+', depth)
                self.remove_package(curr.name, recurse=True, depth=depth, reloading=True)
            # if a package of this type is already active and
            # A) the version requested is the same OR
            # B) a specific version was not requested
            elif not package.explicit_version or curr.version == package.version:
                #self._status('keeping', curr.fullname, ' ', depth)
                # reload if incorrect version of dependencies are set
                reloading = False
                for pkg in package.get_dependencies():
                    try:
                        pkg.version
                    except InvalidPackageVersion:
                        # error raised when package not active
                        reloading = True
                        break
                if reloading:
                    self._status('reloading', package.fullname, '+', depth)
                    self.remove_package(curr.name, depth=depth, reloading=True)
                else:
                    return
            else:
                reloading = True
                self._status('switching', 
                             '%s --> %s' % (curr.fullname, package.version)
                             , '+', depth)
                self.remove_package(curr.name, depth=depth, reloading=True)

        if not reloading:
            self._status('adding', package.fullname, '+', depth)
        self._added.append(package)

        self._exec_package(package, depth=depth)

        del package.versions
        del package.config
        self.shelf[package.name] = package
        
        if reloading:
            # if we just reloaded this package, also reload the dependents
            for dependent in package.get_dependents():
                req_ver = package.required_version(dependent.name)
                if req_ver:
                    if req_ver != package.version:
                        # TODO: prepend dependent's variables
                        logger.warn('WARNING: %s requires %s' % (dependent.fullname, _joinname(package.name, req_ver)))
                else:
                    self.add_package(dependent.fullname, depth=depth+1, force=True)
        return package

    def remove_package(self, name, recurse=False, depth=0, reloading=False):
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
        
        if not reloading:
            self._status('removing', package.fullname, '-', depth)
        
        del self.shelf[shortname]
        self._removed.append(package)

        if recurse:
            for sub in package.subpackages:
                self.remove_package(sub, recurse, depth+1)

        elif not reloading:
            for depend in package.get_dependents():
                self.remove_package(depend.fullname, depth=depth+1)
        return package

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
            return [_joinname(package, versions[package])]
        else:
            print "package %s is not currently active" % package
            return []
    else:
        return [_joinname(pkg, versions[pkg]) for pkg in sorted(versions.keys())]