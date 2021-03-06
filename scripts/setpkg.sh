
[[ -z $SETPKG_ROOT ]] && {
    # This will only have any point if it's sourced, so just use $BASH_SOURCE[0]
    thisfile=$(python -c "import os;print os.path.normcase(os.path.normpath(os.path.realpath(os.path.abspath('''${BASH_SOURCE[0]}'''))))")
    export SETPKG_ROOT=$(dirname $(dirname $thisfile))
}

[[ $SETPKG_PATH ]] || export SETPKG_PATH=$SETPKG_ROOT/packages

[[ $PYTHONPATH ]] && export PYTHONPATH=$SETPKG_ROOT/python:$PYTHONPATH || export PYTHONPATH=$SETPKG_ROOT/python

[[ $SETPKG_PYTHONBIN ]] || export SETPKG_PYTHONBIN=$(which python)

# Bash aliases are not inherited, unlike tcsh aliases
# Instead, make them functions and export with "export -f"
function pkg {
    eval `$SETPKG_PYTHONBIN $SETPKG_ROOT/bin/setpkgcli --shell bash --pid $$ "$@"`
}
export -f pkg

function setpkg {
    pkg set "$@"
}
export -f setpkg

function unsetpkg {
    pkg unset "$@"
}
export -f unsetpkg

function runpkg {
    pkg run "$@"
}
export -f runpkg

function pkgs {
    pkg ls "$@"
}
export -f pkgs

function allpkgs {
    pkg ls --all "$@"
}
export -f allpkgs

function addenv {
    pkg env prepend "$@"
}
export -f addenv

function delevn {
    pkg env pop "$@"
}
export -f delevn

# system aliases
pkg system-alias

_pkg() 
{
    local cur prev opts base
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="set unset info ls"

    case "${prev}" in
        set)
        local packages=`pkg ls --all --aliases`
        COMPREPLY=( $(compgen -W "${packages}" -- ${cur}) )
            return 0
            ;;
        unset)
        local active_packages=`pkg ls`
        COMPREPLY=( $(compgen -W "${active_packages}" -- ${cur}) )
            return 0
            ;;
        *)
        ;;
    esac

    COMPREPLY=($(compgen -W "${opts}" -- ${cur}))  
    return 0
}

complete -F _pkg pkg

_setpkg() 
{
    local cur packages
    cur="${COMP_WORDS[COMP_CWORD]}"
    COMPREPLY=()

    packages=`pkg ls --all --aliases`
    COMPREPLY=( $(compgen -W "${packages}" -- ${cur}) )

    return 0
}

complete -F _setpkg setpkg

_unsetpkg() 
{
    local cur packages
    cur="${COMP_WORDS[COMP_CWORD]}"
    COMPREPLY=()

    packages=`pkg ls`
    COMPREPLY=( $(compgen -W "${packages}" -- ${cur}) )

    return 0
}

complete -F _unsetpkg unsetpkg

