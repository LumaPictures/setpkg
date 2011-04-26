~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
setpkg
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An environment variable management system written in python. The system is based around .pykg files: python
scripts executed in a special environment, containing python ini-style configuration headers. It consists
of a python API and a command-line utility.

Overview:
- one package file per application, written in python
- tracks dependencies between packages (for example, changing maya versions can auto-change python versions)
- tracks sub-packages (dependents)
- knows to reload a package file when the file has been edited
- using relative paths allows it to be used as a more flexible replacement for maya's module system
- understands setting, prepending, and appending to env variables, and can properly undo each of these actions

Command-line utility:
- pkg set: used to set the environment in the current shell (tcsh, csh, bash, sh, DOS)
  - great for setting up build environments
- pkg info: provides feeback on what packages are set, what environment variables they modify
- pkg run: sets up an environment then executes an application
- tab completion of packages
- sessions are properly inherited in child shells 
- can auto-create system aliases for app launching (e.g. alias maya-2011='pkg run maya-2011')

Python Module:
- sets os.environ
- can generate a dictionary for passing to subprocess.Popen

==================================
pykg files
==================================

Typically, a single .pykg file is written for each application to be managed,
and placed on the SETPKG_PATH. When adding a package using the setpkg module or
command line tool, if the requested version of the package is not active, the
.pykg file is executed. Differences per OS, architecture, application
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
        to easily provide utility functions for use within the pykg file, without
        the need to explicitly import it. keep in mind that the setpkgutil module
        must be on the ``PYTHONPATH`` before it can be used.

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

``SETPKG_ROOT`` :
    Setpkg is comprised of several parts:
        - a python module: ``python/setpkg.py``
        - a command line python executable: ``bin/setpkgcli``
        - shell-specific startup scripts: ``scripts/setpkg.sh``, ``scripts/setpkg.csh``, etc

    The environment variable ``SETPKG_ROOT`` should be set to the directory containing
    all of these parts, usually called 'setpkg'.  This environment variable must be
    set before the shell-specific startup scripts are called.

``SETPKG_PATH`` :
    Search path for ``.pykg`` files. defaults to ``$SETPKG_ROOT/packages``

``SETPKG_PYTHONBIN`` :
    Location of the python interpreter to use with setpkg. setpkg cannot use the python
    interpreter on the executable ``PATH`` as this variable might change, and incompatibilities
    between versions of python are known to cause problems. If not set, the full path to the python
    binary found at startup (using ``which python``)  will be stored in this variable.

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

In one of tcsh's startup scripts (/etc/csh.login, /etc/csh.cshrc, ~/.tcshrc, etc) add the
following lines::

    setenv SETPKG_ROOT /path/to/setpkg
    setenv SETPKG_PATH /path/to/pykg_dir:/path/to/other/pykg_dir
    source $SETPKG_ROOT/scripts/setpkg.csh
