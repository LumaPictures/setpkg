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
Configuration Header
----------------------------------

The configuration header is a specialized module-level python docstring written in
 `ConfigParser <http://http://docs.python.org/library/configparser.html>`_ ini-syntax.

An example for Nuke might look like this::

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

main
====

Used to set global options

    executable-path :
        name of the executable for the package, used by ``pkg run``
    
    version-regex :
        validates the version and splits it into components provided as VERSION_PARTS (see below)
        
    versions-from-regex :
        whether to allow versions which are not explicitly listed in versions
        (see below) but do match the version-regex (if it is provided)
    
    default-version :
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

    [versions]
    6.0v2 =
    6.0v1 =
    5.2v3 =
    5.2v1 =
    5.1v6 =
    5.1v4 =

aliases
=======

Alternate names for versions. These are valid to use
anywhere a version is expected, including as the ``default-version``.

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
        first dash ``-`` in the package name.

    VERSION :
        a string containing the current version being set; considered everything
        after the first dash ``-`` in the package name.

    VERSION_PARTS :
        a tuple of version parts if the version string was
        successfully parsed by the ``version-regex`` config variable, if set;
        otherwise, None

    LOGGER :
        the logger object for this module. normal print statements can also be
        used, but the logger provides log levels (error, warn, info, debug) and
        can also be configured to log to a file.

    platform module :
        the contents of the builtin ``platform`` module
        (equivalent of ``from platform import *``)

    setpkgutil module :
        contents of ``setpkgutil`` module, if it exists. this module can be used
        to easily provide utility functions for use within the pykg file. keep
        in mind that the setpkgutil module must be on the ``PYTHONPATH`` before
        it can be used.

----------------------------------
Body
----------------------------------

set a variable, overriding any pre-existing value::
    env.MY_VAR = 'foo'

prepend to a variable, using os-specific variable separators 
( ``:`` on linux/max and ``;`` on windows)::
    env.MY_VAR += 'bar'

All paths used within pykg files should use unix-style forward slashes. On
Windows platforms, they will be converted to backslashes.

Relative paths will be expanded relative to the pykg file, which is useful for
creating maya module-like pykg files. To do this, the parent package simply sets
``SETPKG_PATH`` to a location containing additional pykg files.

==================================
Commandline Tools
==================================

The core command is called ``pkg``, which has several sub-commands, notably ``set``,
``unset``, ``ls``, ``run``, and ``info`` (call ``pkg -h`` for details)

here's a simple example, using the Nuke package file outlined above::

    $ pkg set nuke             
    adding:     [+]  nuke-6.1v2                                          
    adding:     [+]    python-2.5                                        
    adding:     [+]      lumaTools-1.0                                   
    adding:     [+]      pyexternal-1.0                                  
    adding:     [+]        pymel-1.0                                     
    adding:     [+]    djv-0.8.3.p2                                      
    $ pkg ls
    djv-0.8.3.p2
    lumaTools-1.0
    nuke-6.1v2
    pyexternal-1.0
    pymel-1.0
    python-2.5
    $ setpkg nuke-6.0v6       
    switching:  [+]  nuke-6.1v2 --> 6.0v6                                
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
    $ pkg unset nuke
    removing:   [-]  nuke-6.0v6

There are also several handy aliases available:

========  =========== 
alias     cmd
========  =========== 
setpkg    pkg set
unsetpkg  pkg unset
runpkg    pkg run
pkgs      pkg ls
========  ===========

==================================
Installation
==================================

----------------------------------
Environment Variables
----------------------------------

``SETPKG_ROOT``
    Setpkg is comprised of several parts:
        - a python module: ``python/setpkg.py``
        - a command line python executable: ``bin/setpkgcli``
        - shell-specific startup scripts: ``scripts/setpkg.sh``, ``scripts/setpkg.csh``, etc

    The environment variable ``SETPKG_ROOT`` should be set to the directory containing
    all of these parts (usually called 'setpkg').  This environment variable must be
    set before the shell-specific startup scripts are called.

``SETPKG_PATH``
    search path for ``.pykg`` files. defaults to ``$SETPKG_ROOT/packages``

----------------------------------
OSX/Linux
----------------------------------

Bash
====

In one of bash's startup scripts (/etc/profile, ~/.bashrc, ~/.bash_profile, etc) add the
following lines::

    export SETPKG_ROOT=/path/to/setpkg
    export SETPKG_PATH=/path/to/pykg_dir:/path/to/other/pykg_dir
    source $SETPKG_ROOT/scripts/setpkg.sh

Tcsh
====

In one tcsh's startup scripts (/etc/csh.login, /etc/csh.cshrc, ~/.tcshrc, etc) add the
following lines::

    setenv SETPKG_ROOT /path/to/setpkg
    setenv SETPKG_PATH /path/to/pykg_dir:/path/to/other/pykg_dir
    source $SETPKG_ROOT/scripts/setpkg.csh

"""

# TODO:
# colorized output (could be added to the logger?)
# windows: use getpids.exe to get parent id to allow per-process setpkg'ing like on posix
# windows: add --global flag to set environment globally (current behavior)

from __future__ import with_statement
import os
import posixpath
import ntpath
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
import binascii
import zlib
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
    def __get__(cls, self, type=None): #@NoSelf
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

#===============================================================================
# Shell Classes
#===============================================================================

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
        # bash aliases don't export to subshells; so instead define a function,
        # then export that function
        return "%(key)s() { %(value)s; };\nexport -f %(key)s;" % locals()

class Tcsh(Shell):
    def setenv(self, key, value):
        return "setenv %s %s;" % ( key, value )
    def unsetenv(self, key):
        return "unsetenv %s;" % ( key, )
    def alias(self, key, value):
        return "alias %s '%s';" % ( key, value)

class WinShell(Shell):
    # These are variables where windows will construct the value from the value
    # from system + user + volatile environment values (in that order)
    WIN_PATH_VARS = ['PATH', 'LibPath', 'Os2LibPath']
    
    def __init__(self, set_global=False):
        self.set_global = set_global
    def setenv(self, key, value):
        value = value.replace('/', '\\\\')
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
            # If we have a path variable, make sure we don't include items
            # already in the user or system path, as these items will be 
            # duplicated if we do something like:
            #   env.PATH += 'newPath'
            # ...and can lead to exponentially increasing the size of the
            # variable every time we do an append
            # So if an entry is already in the system or user path, since these
            # will proceed the volatile path in precedence anyway, don't add
            # it to the volatile as well
            if key in self.WIN_PATH_VARS:
                sysuser = set(self.system_env(key).split(os.pathsep))
                sysuser.update(self.user_env(key).split(os.pathsep))
                new_value = []
                for val in value.split(os.pathsep):
                    if val not in sysuser and val not in new_value:
                        new_value.append(val)
                volatile_value = os.pathsep.join(new_value)
            else:
                volatile_value = value
            # exclamation marks allow delayed expansion
            quotedValue = subprocess.list2cmdline([volatile_value])
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
    
    def user_env(self, key):
        return executableOutput(['setenv', '-u', key])
    
    def system_env(self, key):
        return executableOutput(['setenv', '-m', key])

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

#===============================================================================
# Environment Classes
#===============================================================================

class EnvironSwapper(object):
    '''Temporarily sets os.environ to use a 'fake' environment
    
    If no environ is explicitly given, a copy of the current os.environ is used.
    
    Intended for use with the 'with' statement
    
    >>> from __future__ import with_statement
    >>> os.environ['TESTVAR'] = 'orig'
    >>> with EnvironSwapper():
    ...     os.environ['TESTVAR'] = 'new flava'
    ...     os.environ['TESTVAR']
    'new flava'
    >>> os.environ['TESTVAR']
    'orig'
    '''
    def __init__(self, environ=None):
        if environ is None:
            environ = dict(os.environ)
        self.oldEnviron = os.environ
        self.newEnviron = environ
    
    def __enter__(self):
        self.oldEnviron = os.environ
        os.environ = self.newEnviron
    
    def __exit__(self, *args):
        os.environ = self.oldEnviron

def _abspath(root, value):
    # not all variables are paths: only absolutize if it looks like a relative path
    if root and \
        (value.startswith('./') or \
        ('/' in value and not (posixpath.isabs(value) or ntpath.isabs(value)))):
        value = os.path.join(root, value)
    return value

def _expand(value, strip_quotes=False, environ=None):
    # use posixpath because setpkg expects posix-style paths and variable expansion
    # (on windows: os.path.expandvars will not expand $FOO-x64)
    if environ is None:
        expanded = posixpath.expandvars(value)
    else:    
        with EnvironSwapper(environ):
            expanded = posixpath.expandvars(value)
    expanded = os.path.normpath(os.path.expanduser(expanded))
    if strip_quotes:
        expanded = expanded.strip('"')
    return expanded

def _split(value):
    return value.split(os.pathsep)

def _join(values):
    return os.pathsep.join(values)

def _nativepath(path):
    return os.path.join(path.split('/'))

def _ntpath(path):
    return ntpath.sep.join(path.split(posixpath.sep))

def _posixpath(path):
    return posixpath.sep.join(path.split(ntpath.sep))

def _prep_env_args(value, expand, root, environ):
    if value is not None:
        if isinstance(value, EnvironmentVariable):
            value = value.value()
        else:
            value = str(value)
        if expand:
            value = _expand(value, strip_quotes=True, environ=environ)
        value = _abspath(root, value)
    
    if environ is None:
        environ = os.environ
    return value, environ

def prependenv(name, value, expand=True, no_dupes=False, root=None, environ=None):
    value, environ =  _prep_env_args(value, expand, root, environ)

    if name not in environ:
        environ[name] = value
    else:
        current_value = environ[name]
        parts = _split(current_value)
        if no_dupes:
            if expand:
                expanded_parts = [_expand(x, environ=environ) for x in parts]
            else:
                expanded_parts = parts
            if value not in expanded_parts:
                parts.insert(0, value)
                new_value = _join(parts)
                environ[name] = new_value
        else:
            parts.insert(0, value)
            new_value = _join(parts)
            environ[name] = new_value
           
    # update_pypath
    if name == 'PYTHONPATH':
        sys.path.insert(0, value)            
    #print "prepend", name, value
    return value

def appendenv(name, value, expand=True, no_dupes=False, root=None, environ=None):
    value, environ =  _prep_env_args(value, expand, root, environ)

    if name not in environ:
        environ[name] = value
    else:
        current_value = environ[name]
        parts = _split(current_value)
        if no_dupes:
            if expand:
                expanded_parts = [_expand(x, environ=environ) for x in parts]
            else:
                expanded_parts = parts
            if value not in expanded_parts:
                parts.append(value)
                new_value = _join(parts)
                environ[name] = new_value
        else:
            parts.append(value)
            new_value = _join(parts)
            environ[name] = new_value
            
    # update_pypath
    if name == 'PYTHONPATH':
        sys.path.append(value)
    #print "append", name, value
    return value

def prependenvs(name, value, root=None, environ=None):
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
        prependenv(name, part, root=root, environ=environ)
    return value

def setenv(name, value, expand=True, root=None, environ=None):
    value, environ =  _prep_env_args(value, expand, root, environ)

    environ[name] = value
    #print "set", name, value
    return value

def unsetenv(name, environ=None):
    environ =  _prep_env_args(None, False, None, environ)[1]
    return environ.pop(name)

def popenv(name, value, expand=True, root=None, environ=None, from_end=False):
    value, environ =  _prep_env_args(value, expand, root, environ)

    try:
        current_value = environ[name]
    except KeyError:
        return
    else:
        parts = _split(current_value)
        if from_end:
            reverse_parts = list(reversed(parts))
            try:
                index = -( reverse_parts.index(value) + 1 )
            except ValueError:
                return
        else:
            try:
                index = parts.index(value)
            except ValueError:
                return
        if len(parts) == 1:
            del environ[name]
        else:
            parts.pop(index)
            environ[name] = _join(parts)
    #print "popenv", name, value
    return value

class Environment(object):
    '''
    provides attribute-style access to an environment dictionary.

    combined with EnvironmentVariable class, tracks changes to the environment
    
    Always linked to a package, since it tracks changes to the environment that
    a given package makes.
    '''
    def __init__(self, package, root=None):
        self.__dict__['_package'] = package
        # use posixpath internally
        self.__dict__['_root'] = _posixpath(root) if root else root
        self.__dict__['_env_vars'] = {}

    def __getattr__(self, attr):
        # For things like '__class__', for instance
        if attr.startswith('__') and attr.endswith('__'):
            try:
                self.__dict__[attr]
            except KeyError:
                raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, attr))
        return self.__env__get__(attr)
    
    def __env__get__(self, attr):
        env_vars = self.__dict__['_env_vars']
        if attr not in env_vars:
            env_vars[attr] = EnvironmentVariable(attr, self)
        return env_vars[attr]

    def __setattr__(self, attr, value):
        # For things like '__class__', for instance
        if attr.startswith('__') and attr.endswith('__'):
            super(Environment, self).__setattr__(attr, value)
        self.__env__set__(attr, value)
        
    def __env__set__(self, attr, value):
        if isinstance(value, EnvironmentVariable) and value.name == attr:
            # makes no sense to set ourselves. most likely a result of:
            # env.VAR += value
            return
        self.__env__get__(attr).set(value)
        
    def __delattr__(self, attr):
        # For things like '__class__', for instance
        if attr.startswith('__') and attr.endswith('__'):
            super(Environment, self).__delattr__(attr)
        self.__env__unset__(attr)
        
    def __env__unset__(self, attr):
        self.__env__get__(attr).unset()
        del self.__dict__['environ'][attr]

    def __contains__(self, attr):
        return attr in self.environ

    def __str__(self):
        return pprint.pformat(self.environ)
    
    def __getstate__(self):
        # Clean out any _env_vars that we haven't acted on
        vars = self.__dict__['_env_vars']
        for name, var in vars.items():
            if not var._actions:
                vars.pop(name)
        return self.__dict__
    
        
class EnvironmentVariable(object):
    '''
    class representing an environment variable

    combined with Environment class, tracks changes to the environment
    '''
    
    def __init__(self, name, environ_obj):
        self._name = name
        self._environ_obj = environ_obj
        self._actions = []

    def __str__(self):
        return '%s = %s' % (self._name, self.value())

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._name)

    def __nonzero__(self):
        return bool(self.value())

    @property
    def name(self):
        return self._name
    
    @property
    def root(self):
        return self._environ_obj.__dict__['root']
    
    @property
    def environ(self):
        return self._environ_obj.__dict__['_package'].environ

    def prepend(self, value, **kwargs):
        return self._actions.append(Prepend(self._environ_obj, self._name, value,
                                           **kwargs))

    def append(self, value, **kwargs):
        return self._actions.append(Append(self._environ_obj, self._name, value,
                                          **kwargs))

    def set(self, value, **kwargs):
        return self._actions.append(Set(self._environ_obj, self._name, value,
                                       **kwargs))

    def unset(self, **kwargs):
        return self._actions.append(Set(self._environ_obj, self._name, None,
                                       **kwargs))
        
    def pop(self, **kwargs):
        return self._actions.append(Pop(self._environ_obj, self._name, None,
                                        **kwargs))
        

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
        return self.environ.get(self._name, None)

    def split(self):
        # FIXME: value could be None.  should we return empty list or raise an error?
        value = self.value()
        if value is not None:
            return _split(value)
        else:
            return []

class Action(object):
    '''Stores information about a change to an environment variable
    
    The changes are made when the action is created; to undo, call the undo
    method
    '''
    def __init__(self, environ_obj, attr, val, undo=True, **kwargs):
        kwargs['environ'] = environ_obj.__dict__['_package'].environ
        kwargs['root'] = environ_obj.__dict__['_root']
        self.undo_data = self._do_action(attr, val, **kwargs)
        if not undo:
            self.undo_data = ''
        
    # For data compactness, as this is pickled, don't store attr name on
    # the Action instance, but explicitly pass it in on undo
    def undo(self, environ_obj, attr):
        kwargs = {}
        kwargs['environ'] = environ_obj.__dict__['_package'].environ
        kwargs['root'] = environ_obj.__dict__['_root']
        kwargs['expand'] = False
        self._undo_action(attr, self.undo_data, **kwargs)

class Prepend(Action):
    def _do_action(self, attr, val, **kwargs):
        return prependenv(attr, val, **kwargs)
    def _undo_action(self, attr, val, **kwargs):
        logger.debug("undoing Prepend - %s - %s - %r" % (attr, val, kwargs['environ'].get(attr)))
        popenv(attr, val, from_end=False, **kwargs)
        
class Append(Action):
    def _do_action(self, attr, val, **kwargs):
        return appendenv(attr, val, **kwargs)
    def _undo_action(self, attr, val, **kwargs):
        logger.debug("undoing Append - %s - %s - %r" % (attr, val, kwargs['environ'].get(attr)))
        popenv(attr, val, from_end=True, **kwargs)
        
class Set(Action):
    def _do_action(self, attr, val, **kwargs):
        orig_val = kwargs['environ'].get(attr)
        setenv(attr, val, **kwargs)
        return orig_val
    def _undo_action(self, attr, val, **kwargs):
        logger.debug("undoing Set - %s - %s - %r" % (attr, val, kwargs['environ'].get(attr)))
        setenv(attr, val, **kwargs)
        
# Unset is done by Set(attr, None)
#
#class Unset(Action):
#    def _do_action(self, attr, val, **kwargs):
#        return unsetenv(attr, val, environ=kwargs['environ'])
#    def _undo_action(self, attr, val, **kwargs):
#        setenv(attr, val, from_end=True, **kwargs)

class Pop(Action):
    def _do_action(self, attr, val, **kwargs):
        self.from_end = kwargs.pop('from_end', False)
        return popenv(attr, val, from_end=self.from_end, **kwargs)
    def _undo_action(self, attr, val, **kwargs):
        logger.debug("undoing Pop - %s - %s - %r" % (attr, val, kwargs['environ'].get(attr)))
        if self.from_end:
            appendenv(attr, val, **kwargs)
        else:
            prependenv(attr, val, **kwargs)
        

#===============================================================================
# Package Files
#===============================================================================

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

class PackageRemovedError(PackageError):
    def __init__(self, package):
        self.package = package
    def __str__(self):
        return 'Package %s has been removed' % self.package

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

class BasePackage(object):
    def __init__(self, session=None, root=None):
        if session is None:
            session = Session()
        self._session = session
        self._environ_obj = Environment(self, root=root)
    @property
    def environ(self):
        return self._session.environ
    
    def environ_vars(self):
        return self._environ_obj.__dict__['_env_vars']

    # To save space, remove the session object from the package (otherwise,
    # we end up pickling the whole environment!)
    # Note that this means when unpickling a package, there will be no _session
    # variable - it is the unpickler's responsibility to set this!
    def __getstate__(self):
        pickle_dict = dict(self.__dict__)
        session = pickle_dict.pop('_session', None)
        return pickle_dict

            
class FakePackage(BasePackage):
    '''
    A package that does not exist on disk
    '''
    def __init__(self, name, version, session=None):
        self.name = name,
        self.version = version
        self.versions = [self.version]
        super(FakePackage, self).__init__(session=session)

    @propertycache
    def hash(self):
        return _joinname(self.name, self.version)

class RealPackage(BasePackage):
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
        val = self.environ.get(var, None)
        if val:
            return [PackageInterface(pkg, session=self._session)
                    for pkg in _split(val)]
        else:
            return []

    def get_dependents(self):
        '''
        return a list of (dependent, explicit_version)
        
        explicit_version will be True if this dependent specified a version
        of the current package
        '''
        try:
            return [PackageInterface(name, session=self._session)
                    for name in _split(self.environ['SETPKG_DEPENDENTS_%s' % self.name])]
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
                for pkg in _split(self.environ['SETPKG_DEPENDENCIES_%s' % self.name])])
        except KeyError:
            return {}

    def required_version(self, package):
        return PackageInterface(package, session=self._session).get_dependency_versions()[self.name]

    def is_active(self):
        logger.debug("%s is_active: %s" % (self.name, VER_PREFIX + self.name in self.environ))
        return VER_PREFIX + self.name in self.environ

    def __eq__(self, other):
        # use file instead?
        return (self.name, self.version) == (other.name, other.version)

class PackageInterface(RealPackage):
    '''
    Represents an active package
    '''
    def __init__(self, name, session=None):
        super(PackageInterface, self).__init__(session=session)
        self.origname = name
        self.name, self._version = _splitname(name)
        # TODO: assert version

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.origname)

    @propertycache
    def hash(self):
        try:
            version, hash = self.environ[VER_PREFIX + self.name].split(META_SEP)
        except KeyError:
            # TODO: different error
            raise PackageRemovedError(self.name)
        self.version = version
        return hash

    @propertycache
    def version(self):
        try:
            version, hash = self.environ[VER_PREFIX + self.name].split(META_SEP)
        except KeyError:
            raise PackageRemovedError(self.name)
        
        if self._version:
            if self._version != version:
                raise InvalidPackageVersion(self.name, self._version, 'active version is %s' % version)
        self.hash = hash
        return version

    def add_dependent(self, package):
        var = 'SETPKG_DEPENDENTS_%s' % self.name
        prependenv(var, package.name)

class Package(RealPackage):
    '''
    Class representing a .pykg package file on disk.
    '''
    # allowed characters: letters, numbers, period, dash, underscore
    VERSION_RE = re.compile('[a-zA-Z0-9\.\-_]+$')
    def __init__(self, file, version=None, session=None):
        '''
        instantiate a package from a package file.

        Parameters
        ----------
        version : str
            if version is not provided, the default version is
            automatically determined from the `default-version` configuration
            variable in the package header. If that is not set and the lists of the
            `versions` configuration variable is exactly one, that value is used,
            otherwise an error is raised.
        '''
        self.file = file
        parent, basename = os.path.split(file)
        self.name = os.path.splitext(basename)[0]
        self._version = version
        self._parent = None
        self._dependencies = []
        self._dependents = []
        super(Package, self).__init__(session=session, root=parent)

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
            version = self.default_version
        if version not in self.versions and version in self.aliases:
            # expand aliases
            version = self.aliases[version]
        if version not in self.versions:
            regex = self.version_regex
            if (not regex
                    or not self.version_from_regex
                    or not regex.match(version)):
                if not self.explicit_version:
                    version = '%s (default)' % version
                ver_choices = ', '.join(self._session.list_package_versions(self,
                                                                aliases=True,
                                                                regexp=True))
                raise InvalidPackageVersion(self.name, version,
                                            '(valid choices are %s)' % ver_choices)
        return version
    
    @propertycache
    def default_version(self):
        version = self.environ.get('SETPKG_%s_DEFAULT_VERSION' % self.name.upper())
        if not version:
            if self.config.has_option('main', 'default-version'):
                version = self.config.get('main', 'default-version')
            elif len(self.versions) == 1:
                version = self.versions[0]
            else:
                raise PackageError(self.name, "no 'default-version' specified in package header ([main] section)")
        return version

    @propertycache
    def config(self):
        '''
        read the header of a package file into a python ConfigParser
        '''
        # Would like to use defaults of ConfigParser, ie:
        #    config = ConfigParser({'main.versions-from-regex':False})
        # ...but doing so ALSO sets the the default value for main.version to
        # False... probably I just don't understand how to use the defaults...
        # but can't find good docs / examples...
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
        regexp = self.version_regex
        if not regexp:
            regexp = self.VERSION_RE
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
    def version_regex(self):
        if self.config.has_option('main', 'version-regex'):
            return re.compile('(?:' + self.config.get('main', 'version-regex') +')$')
        return None
    
    @propertycache
    def version_from_regex(self):
        if (self.version_regex and
                self.config.has_option('main', 'versions-from-regex')):
            return self.config.getboolean('main', 'versions-from-regex')
        return False
                    
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
        reg = self.version_regex
        if reg:
            try:
                return reg.match(self.version).groups()
            except AttributeError:
                logger.warn('could not split version using version-regex %r' % reg)
        return None
                
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
        return [ PackageInterface(pkg, session=self._session) for pkg in self._read_packagelist('requires')]

#===============================================================================
# SessionStorage
#===============================================================================
class SessionStorage(object):
    '''Base class for storing persistent session data.
    
    Should have a dictionary-like interface
    
    Actual implentation should subclass from this.
    '''
    # Holds the session's pid
    SESSION_VAR = 'SETPKG_SESSION'
    
    def __init__(self, session):
        '''Generally, this should not be overridden - override pre_init
        initialize_data, or post_init instead
        '''
        self.session = session
        self.setpkg_pkg = None
        self.pre_init()
        if self.needs_data_init():
            self.initialize_data()
        self.post_init()
            
    def init_type(self):
        '''Returns 'new' if no setpkg has been run in this or any parent process,
        'child' if setpkg has not been run in this process, but has in a parent,
        or 'done' if setpkg has been run in this process
        ''' 
        pid = self.session.environ.get(self.SESSION_VAR)
        if not pid:
            return 'new'
        elif pid != self.session.pid:
            return 'child'
        else:
            return 'done'
        
    def needs_data_init(self):
        return True
            
    def initialize_data(self):
        '''Does whatever needs to be done to create 'new' session data
        
        called the first time data is needed within a given process
        '''
        self.setpkg_pkg = FakePackage('setpkg', version='2.0',
                                      session=self.session)
        self.session._added.append(self.setpkg_pkg)
        getattr(self.setpkg_pkg._environ_obj, self.SESSION_VAR).set(self.session.pid)
    
    def pre_init(self):
        pass

    def post_init(self):
        pass

    
    def __getitem__(self, key):
        raise NotImplementedError
    def __setitem__(self, key, val):
        raise NotImplementedError
    def __delitem__(self, key):
        raise NotImplementedError
    def __contains__(self, key):
        raise NotImplementedError

class SessionShelf(SessionStorage):
    '''Persistent storage using 'shelf' files on disk
    '''
    SESSION_PREFIX = 'setpkg_session_'
    SHELF_FILE_VAR = 'SETPKG_SHELF'

    def __getitem__(self, key):
        return self.shelf[key]
    def __setitem__(self, key, val):
        self.shelf[key] = val
    def __delitem__(self, key):
        del self.shelf[key]
    def __contains__(self, key):
        return key in self.shelf
    
    def pre_init(self):
        self.shelf = self._open_shelf()

    def needs_data_init(self):
        return self.init_type() != 'done'
    
    def initialize_data(self):
        super(SessionShelf, self).initialize_data()
        self.shelf = self._open_shelf()
        getattr(self.setpkg_pkg._environ_obj, self.SHELF_FILE_VAR).set(self.filename)
    
    def _open_shelf(self, protocol=None, writeback=False):
        """
        """
        pid = self.session.pid
        environ = self.session.environ
        if self.SHELF_FILE_VAR in environ:
            filename = environ[self.SHELF_FILE_VAR]
            # see if our pid differs from the existing
            old_pid = filename.rsplit('_')[-1]
            if pid != old_pid:
                # make a unique copy for us
                old_filename = filename
                filename = os.path.join(tempfile.gettempdir(), (self.SESSION_PREFIX + pid))
                logger.info('copying cache from %s to %s' % (old_filename, filename))
                # depending on the underlying database type used by shelve,
                # the file may actually be several files
                for suffix in ['', '.bak', '.dat', '.dir', '.db']:
                    full_old_filename = old_filename + suffix
                    if os.path.exists(full_old_filename):
                        # can have some permissions issues (ie, with chmod)
                        # if the file already exists... make life easier and
                        # just delete it
                        full_new_filename = filename + suffix
                        if os.path.isfile(full_new_filename):
                            os.remove(full_new_filename)
                        shutil.copy(full_old_filename, full_new_filename)
            # read an existing shelf
            flag = 'w'
            logger.info( "opening existing session %s" % filename )
        else:
            filename = os.path.join(tempfile.gettempdir(), (self.SESSION_PREFIX + pid))
            # create a new shelf
            flag = 'n'
            logger.info( "opening new session %s" % filename )

        self.filename = filename
        return shelve.DbfilenameShelf(filename, flag, protocol, writeback)

class SessionEnv(SessionStorage):
    '''Persistent storage using environment variables
    '''
    SESSION_DATA_PREFIX = 'SETPKG_SESSION_DATA_'

    # Would like to make these per-shell, but that would mean passing down the
    # shell somehow... seems like too much work for a limited benefit
    
    # The Microsoft / Windows thing is just for a bug with platform.system(),
    # which returned 'Microsoft' for Vista, and 'Windows' for pretty much
    # all other windows flavors
    MAX_VAR_SIZES = {'Windows':1000,
                     # This limit is for TCSH...
                     # bash on Darwin seems unlimited (or at least, very large)
                     'Darwin':4000,
                     'Linux':120000}
    
    # Length testers:
    # tcsh
    #   setenv LONG_VAR `python -c "print 'A'*4096"` && echo $LONG_VAR
    # bash
    #   export LONG_VAR=`python -c "print 'set LONG_VAR=%s'%'A'*4096" && echo $LONG_VAR
    # dos
    #   python -c "print 'set LONG_VAR=%s'%('A'*50)" | cmd
     
    
    # Keep this a set value, so if data is pickled by one version of python and
    # read by another, we're ok... just need to make sure that this version is
    # available to all python versions that may run setpkg
    PICKLE_DATA_VER = 2
    
    def __getitem__(self, key):
        return self.read_dict()[key]
    def __setitem__(self, key, val):
        data = self.read_dict()
        data[key] = val
        self.write_dict(data)
    def __delitem__(self, key):
        data = self.read_dict()
        del data[key]
        self.write_dict(data)
    def __contains__(self, key):
        return key in self.read_dict()
    
    def get_data_vars(self):
        data_vars = [x for x in self.session.environ
                     if x.startswith(self.SESSION_DATA_PREFIX)]
        if not data_vars:
            return []

        data_var_nums = [int(x[len(self.SESSION_DATA_PREFIX):])
                         for x in data_vars]
        assert len(data_var_nums) == max(data_var_nums) + 1, "Setpkg session data variables %s* not sequential" % self.SESSION_DATA_PREFIX
        
        vals = []
        for i in xrange(len(data_vars)):
            var = self.SESSION_DATA_PREFIX + str(i)
            vals.append(self.session.environ[var])
        return vals
        

    def read_dict(self):
        rawstr = ''.join(self.get_data_vars())
        if not rawstr:
            return {}
        package_dict = self.binary_to_python(self.alpha_to_binary(rawstr))
        # The packages don't pickle their session, so restore it here
        for obj in package_dict.itervalues():
            if isinstance(obj, BasePackage):
                obj._session = self.session
        return package_dict
    
    def write_dict(self, newdict):
        rawstr = self.binary_to_alpha(self.python_to_binary(newdict))
        remainder = rawstr
        i = 0
        system = platform.system()
        if system == 'Microsoft':
            # Bug with platform.system - Vista reports as 'Microsoft'
            system = 'Windows'
        max_size = self.MAX_VAR_SIZES[system]
        while remainder:
            # We'll start with 1...
            var = self.SESSION_DATA_PREFIX + str(i)
            getattr(self.setpkg_pkg._environ_obj, var).set(remainder[:max_size], undo=False)
            remainder = remainder[max_size:]
            i += 1
        # Remove any old env vars > current size
        while True:
            var = self.SESSION_DATA_PREFIX + str(i)
            if var not in self.session.environ:
                break
            else:
                del self.session.environ[var]
            i += 1

    # Even though pickle.loads/dumps give strings which we could theoretically
    # simply stick into environment variables straight up, we will need to
    # eventually echo all set commands out to the shell, and quoting a string
    # with lots of weird characters (even nulls!) would be a nightmare.
    # Therefore, we encode binary strings to strings with just alpha-numeric
    # characters
    def alpha_to_binary(self, alphastr):
        return binascii.unhexlify(alphastr)
    
    def binary_to_alpha(self, binarystr):
        return binascii.hexlify(binarystr)
    
    def python_to_binary(self, py_obj):
        return zlib.compress(pickle.dumps(py_obj, protocol=self.PICKLE_DATA_VER))
    
    def binary_to_python(self, bin_obj):
        return pickle.loads(zlib.decompress(bin_obj))
        

#===============================================================================
# Session
#===============================================================================
class DefaultSessionMethod(object):
    """
    a decorator which will create and feed in a 'default' Session object if
    invoked from the class
    
    This default Session will have a 'live' (not a copy) of os.environ set as
    it's environ dict (for speed - ie, to avoid a copy of a potentially large
    environment), and so this decorator should be used only on methods which
    will not alter the environment (ie, information gathering methods, such
    as ones which query SETPKG_VERSION_* to see which packages are currently
    set, etc)
    """
    def __init__(self, method):
        self.method = method

    def __get__(self, instance, owner):
        if instance is None:
            # Could have also just done:
            # instance = Session(environ=os.environ)
            # ...since this is only intended to be used on the Session class...
            instance = owner(environ=os.environ)
        def bound_func(*args, **kwargs):
            return self.method(instance, *args, **kwargs)
        return bound_func

class Session(object):
    '''
    A persistent session that manages the adding and removing of packages.

    Utilizes a SessionStorage class to handle serializing / loading / saving
    of persistant data.
    
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
    _sessions = {}
    
    def __new__(cls, pid=None, storage_class=SessionEnv, reuse=True,
                environ=None):
        if pid is None:
            pid = _getppid()
        
        if reuse:
            saved_session = cls._sessions.get(pid)
            if saved_session is not None:
                return saved_session

        if environ is None:
            environ = dict(os.environ)

        self = super(Session, cls).__new__(cls)
        self._added = []
        self._removed = []
        self.out = sys.stderr
        self.pid = pid if pid else _getppid()
        self.filename = None
        self.storage_class = storage_class
        self._environ_dict = environ
        self.entry_level = 0
        
        if reuse:
            cls._sessions[pid] = self
        return self
        
    @property
    def environ(self):
        return self._environ_dict
        
    def __enter__(self):
        #logger.debug( "new session %s" % self.filename )
        self.entry_level += 1
        return self

    def __exit__(self, type, value, traceback):
        self.entry_level -= 1
        if self.entry_level <= 0:
            #logger.debug('session closed')
            self.close()

    def _status(self, action, package, symbol=' ', depth=0):
        #prefix = '   ' * depth + '[%s]  ' % symbol
        prefix = '[%s]  ' % symbol + ('  ' * depth)
        self.out.write(('%s:' % action).ljust(12) + prefix + '%s\n' % (package,))
        logger.info('%s: %s' % (package, action))

    def _exec_package(self, package, depth=0):
        '''
        excecute the pacakge.
         - setup the python globals
         - load the package requirements
         - execfile the package file
         - load package dependents
        ''' 
        g = {}
        # environment
        g['env'] = package._environ_obj

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
        for n in ['is_pkg_set', 'current_version']:
            g[n] = getattr(self, n)

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
            shortname = _splitname(pkg)[0]
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

    def get_package(self, name):
        '''
        find a package on SETPKG_PATH and return a Package class.
    
        Parameters
        ----------
        name : str
            a versioned or unversioned package name
        '''
        shortname, version = _splitname(name)
        return Package(self.find_package_file(shortname), version, session=self)


    def add_package(self, name, parent=None, force=False, depth=0):
        try:
            package = self.get_package(name)
        except PackageError, err:
            logger.error(err)
            return
        shortname = package.name
        curr = PackageInterface(shortname, session=self)
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
        self.storage[package.name] = package
        
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
        curr_version = self.current_version(shortname)
        if curr_version is None:
            raise PackageError(shortname, "package is not currently set")
        package = self.storage[shortname]
        if version:
            if package.version != version:
                raise InvalidPackageVersion(package, version,
                    "cannot be removed because it is not currently set (active version is %s)" % (package.version,))

        if not reloading:
            self._status('removing', package.fullname, '-', depth)

        for name, env_var in package.environ_vars().iteritems():
            for action in reversed(env_var._actions):
                action.undo(package._environ_obj, name)
        
        del self.storage[shortname]
        self._removed.append(package)

        if recurse:
            for sub in package.subpackages:
                self.remove_package(sub, recurse, depth+1)

        elif not reloading:
            for depend in package.get_dependents():
                # Make sure that the package hasn't already been removed
                # because of some other recursive dependency...
                if depend.name in self.current_versions():
                    self.remove_package(depend.fullname, depth=depth+1)
        return package

    @propertycache
    def storage(self):
        return self.storage_class(self)
            
    @property
    def added(self):
        return self._added

    @property
    def removed(self):
        return self._removed
    
    def altered(self, other=None):
        if other is None:
            other = os.environ
            
        # we'll be modifying this, make a copy
        removed = dict(other)
        changed = {}
        for key, val in self.environ.iteritems():
            if val is None:
                # This means the value was deleted... skip
                continue
            old_val = removed.pop(key, None)
            if old_val != val:
                changed[key] = val
        # After popping off all vals in self.environ, removed will have left
        # only values that have been removed...
        return changed, removed
    
    #===========================================================================
    # Info methods
    #===========================================================================
    
    @DefaultSessionMethod
    def _pkgpaths(self):
        if 'SETPKG_PATH' not in self.environ:
            raise ValueError('SETPKG_PATH environment variable not set!')
        return _split(self.environ['SETPKG_PATH'])

    @DefaultSessionMethod
    def _current_data(self, name):
        '''
        return the version and pykg file hash for the given pkg
        '''
        shortname = _shortname(name)
        try:
            data = self.environ[VER_PREFIX + shortname].split(META_SEP)
        except KeyError:
            return (None, None)
        else:
            if len(data) == 1:
                return (data[0], None)
            elif len(data) == 2:
                return tuple(data)
            else:
                raise PackageError(shortname, 'corrupted version data')

    @DefaultSessionMethod
    def is_pkg_set(self, name):
        '''
        return whether the package is set. if a package version is supplied,
        will also check that this is the version is active
        '''
        version = self.current_version(name)
        if not version:
            return False
        ver = _splitname(name)[1]
        if ver:
            return version == ver
        else:
            return True

    @DefaultSessionMethod
    def current_version(self, name):
        '''
        get the currently set version for the given pkg, or None if it is not set
    
        Parameters
        ----------
        name : str
            a versioned or unversioned package name
        '''
        return self._current_data(name)[0]

    @DefaultSessionMethod
    def current_versions(self):
        '''
        return a dictionary of shortname to version for all active packages
        '''
        return dict((key[len(VER_PREFIX):], val.split(META_SEP)[0])
                    for key, val in self.environ.iteritems()
                    if key.startswith(VER_PREFIX) and val is not None)


    @DefaultSessionMethod
    def find_package_file(self, name):
        '''
        given an unversioned package name, search SETPKG_PATH for the .pykg file
    
        Parameters
        ----------
        name : str
            a versioned or unversioned package name
        '''
        for path in self._pkgpaths():
            file = os.path.join(_expand(path), (name + '.pykg'))
            if os.path.exists(file):
                return file
        raise PackageError(name, 'unknown package')

    @DefaultSessionMethod
    def walk_package_files(self):
        # Accomodate for hiearchical setpkg paths - if we've already encountered
        # a given .pykg, don't yield a new one
        discovered = set()
        for path in self._pkgpaths():
            for f in sorted(os.listdir(path)):
                if f.endswith('.pykg') and f not in discovered:
                    discovered.add(f)
                    yield os.path.join(path, f)

    @DefaultSessionMethod
    def list_active_packages(self, package=None, pid=None):
        versions = self.current_versions()
        if package:
            if package in versions:
                return [_joinname(package, versions[package])]
            else:
                logger.warn("package %s is not currently active" % package)
                return []
        else:
            return [_joinname(pkg, versions[pkg]) for pkg in sorted(versions.keys())]

    @DefaultSessionMethod
    def list_package_choices(self, package=None, versions=True, aliases=False,
                             regexp=False):
        '''
        list available packages in NAME-VERSION format.
    
        Parameters
        ----------
        package : str
            name of package to list versions for.  if None, lists all available
            packages and versions
        versions : bool
            whether to list all versions for a package
        aliases : bool
            if versions is True, whether to list all aliases as well
        regexp : bool
            if versions is True, and versions-from-regexp is enabled, whether to list
            this regexp in the versions as well
    
        '''
        packages = []
        if package:
            package_files = [self.find_package_file(package)]
        else:
            package_files = sorted(self.walk_package_files())
    
        if not versions:
            return [ os.path.splitext(os.path.basename(file))[0] for file in package_files]
    
        for package_file in package_files:
            try:
                pkg = Package(package_file, session=self)
                versions = self.list_package_versions(package=pkg, aliases=aliases,
                                                 regexp=regexp)
                packages.extend(_joinname(pkg.name, ver) for ver in versions)
            except PackageError, err:
                logger.debug(str(err))
        return packages

    @DefaultSessionMethod
    def list_package_versions(self, package=None, package_file=None,
                              aliases=False, regexp=False):
        '''list all available versions for a package
        
        Parameters
        ----------
        package : str or Package
            name of package, or Package object to list versions for.
            Exactly one of package and package_file must be provided (and not both) 
        package_file : str
            path of package to list versions for.
            Exactly one of package and package_file must be provided (and not both) 
        aliases : bool
            if versions is True, whether to list all aliases as well
        regexp : bool
            if versions is True, and version-by-regexp is enabled, whether to list
            this regexp in the versions as well
        '''
        if not package or package_file:
            raise PackageError('no package or packageFile given')
        elif package and package_file:
            raise PackageError('both package and packageFile given')
        elif package:
            if isinstance(package, Package):
                package_file = package.file
            else:
                package_file = self.find_package_file(package)
    
        versions = []
        try:
            pkg = Package(package_file, session=self)
            versions = list(pkg.versions)
            if aliases:
                versions.extend(sorted(pkg.aliases))
            if regexp and pkg.version_from_regex:
                ver_re = pkg.version_regex
                if ver_re:
                    versions.append('(regexp:' + ver_re.pattern + ')')
        except PackageError, err:
            logger.debug(str(err))
        return versions

def _update_environ(session, other=None):
    if other is None:
        other = os.environ
    changed, removed = session.altered(other=other)
    for key, val in changed.iteritems():
        other[key] = val
    for key in removed:
        del other[key]
    return changed, removed

def setpkg(packages, force=False, update_pypath=False, pid=None, environ=None):
    """
    Parameters
    ----------
    update_pythonpath : bool
        set to True if changes to PYTHONPATH should be
        reflected in sys.path
        (obselete - ignored - PYTHONPATH changes are always reflected in sys.path)
    force : bool 
        set to True if package should be re-run (unloaded, then
        loaded again) if already loaded
    """
    logger.debug('setpkg %s' % ([force, update_pypath, pid, sys.executable]))
    if isinstance(packages, basestring):
        packages = [packages]
    if environ is None:
        environ = os.environ    
    
    session = Session(pid=pid, environ=dict(environ))
    for name in packages:
        session.add_package(name, force=force)

    return _update_environ(session, other=environ)

def unsetpkg(packages, recurse=False, update_pypath=False, pid=None,
             environ=None):
    """
    Parameters
    ----------
    update_pythonpath : bool
        set to True if changes to PYTHONPATH should be
        reflected in sys.path
        (obselete - ignored - PYTHONPATH changes are always reflected in sys.path)
    force : bool
        set to True if package should be re-run (unloaded, then
        loaded again) if already loaded
    """
    logger.debug('unsetpkg %s' % ([recurse, update_pypath, pid, sys.executable]))
    if isinstance(packages, basestring):
        packages = [packages]
    if environ is None:
        environ = os.environ

    session = Session(pid=pid, environ=dict(environ))
    for name in packages:
        session.remove_package(name, recurse=recurse)

    return _update_environ(session, other=environ)

