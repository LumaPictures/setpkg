@echo off
REM Uncomment that to make less crap print out

REM core commands

REM **************************************************
REM SETPKG_PATH
REM **************************************************

if not defined SETPKG_PATH (goto :DEFAULT_SETPKG_PATH)
if SETPKG_PATH=="" (goto :DEFAULT_SETPKG_PATH)
goto :SETPKG_PATH_DONE

:DEFAULT_SETPKG_PATH
set SETPKG_PATH=%SETPKG_ROOT%\packages

:SETPKG_PATH_DONE

REM **************************************************
REM PYTHONPATH
REM **************************************************

if not defined PYTHONPATH (goto :DEFAULT_PYTHONPATH)
if PYTHONPATH=="" (goto :DEFAULT_PYTHONPATH)

set PYTHONPATH=%PYTHONPATH%;%SETPKG_ROOT%\python
goto :PYTHONPATH_DONE

:DEFAULT_PYTHONPATH
set PYTHONPATH=%SETPKG_ROOT%\python

:PYTHONPATH_DONE

REM These are set as process environment variables, set them
REM as volatile environment variables
setenv -v SETPKG_PATH "%SETPKG_PATH%"
setenv -v PYTHONPATH "%PYTHONPATH%"

REM ------------------
REM TODO: Dos aliases

REM Know of two ways to potentially do DOS 'aliases':
REM doskey name="mycommand args"
REM Using regedit, create a subkey called "ALIASNAME" in
REM "HKLM\SOFTWARE\Microsoft\CurrentVersion\App Paths"
REM with a value of "C:\My\Real\executable.exe"

REM ---Need dos equivalent for these csh commands...

REM set bin = $SETPKG_ROOT/bin
REM alias pkg  'eval `$bin/setpkgcli --shell tcsh --pid $$ \!*`'
REM 
REM alias addenv    'pkg env prepend \!*'
REM alias delenv    'pkg env pop \!*'
REM alias setpkg    'pkg set \!*'
REM alias unsetpkg  'pkg unset \!*'
REM alias runpkg    'pkg run \!*'
REM alias pkgs      'pkg ls \!*'
REM alias allpkgs      'pkg ls --all \!*'

REM # system aliases
REM pkg system-alias

REM ---------------

