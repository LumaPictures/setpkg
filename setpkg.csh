

# core commands
#setenv PATH ${PATH}:`dirname $SETPKG_PATH`/bin
set bin = `dirname $SETPKG_PATH`/bin

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
