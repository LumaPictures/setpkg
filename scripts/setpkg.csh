

# core commands

if ( ! $?SH_PATH ) then
    setenv SETPKG_ROOT `dirname $SETPKG_PATH`
endif

if [ -z "$PYTHONPATH" ]; then
    setenv PYTHONPATH $SETPKG_ROOT/python
else
    setenv PYTHONPATH $PYTHONPATH:$SETPKG_ROOT/python
endif

set bin = $SETPKG_ROOT/bin

alias pkg  'eval `$bin/setpkgcli --shell tcsh --pid $$ \!*`'

alias addenv    'pkg env prepend \!*'
alias delenv    'pkg env pop \!*'
alias setpkg    'pkg set \!*'
alias unsetpkg  'pkg unset \!*'
alias runpkg    'pkg run \!*'

# system aliases
pkg system-alias

# completion
set packages = `pkg ls --aliases`
set base_packages = `pkg ls --base`

complete setpkg  p/1/\$packages/ n/-rehash/\$packages/
complete unsetpkg  p/1/\$base_packages/
