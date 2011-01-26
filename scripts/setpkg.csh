
set called=($_)

echo $called
if ( ! $?SETPKG_ROOT ) then
    # This will only have any point if it's sourced, so just use $BASH_SOURCE[0]
    set sourceArg="${called[2]}"
    set thisfile=`python -c "import os,sys; print os.path.normcase(os.path.normpath(os.path.realpath(os.path.abspath(sys.argv[1]))))" "$called[2]"`
    set thisdir=`dirname $thisfile`
    setenv SETPKG_ROOT `dirname $thisdir`
endif

if ( ! $?SETPKG_PATH ) then
    setenv SETPKG_PATH $SETPKG_ROOT/packages
endif

if ( ! $?PYTHONPATH ) then
    setenv PYTHONPATH $SETPKG_ROOT/python
else
    setenv PYTHONPATH ${PYTHONPATH}:${SETPKG_ROOT}/python
endif

set bin = $SETPKG_ROOT/bin

# core commands

alias pkg       'eval `$bin/setpkgcli --shell tcsh --pid $$ \!*`'
alias debugpkg  'echo `$bin/setpkgcli --shell tcsh --pid $$ \!*`'

alias addenv    'pkg env prepend \!*'
alias delenv    'pkg env pop \!*'
alias setpkg    'pkg set \!*'
alias unsetpkg  'pkg unset \!*'
alias runpkg    'pkg run \!*'
alias pkgs      'pkg ls \!*'
alias allpkgs      'pkg ls --all \!*'

# system aliases
pkg system-alias

# completion
set packages = `pkg ls --aliases`
set base_packages = `pkg ls --base`

complete setpkg  p/1/\$packages/ n/-rehash/\$packages/
complete unsetpkg  p/1/\$base_packages/

