
function pkg { 
    bin=`dirname "$SETPKG_PATH"`/bin
	eval `$bin/setpkgcli --shell bash --pid $$ "$@"`
}

export -f pkg

alias setpkg='pkg set'
alias unsetpkg='pkg unset'
alias runpkg='pkg run'
alias pkgs='pkg ls'
alias addenv='pkg env prepend'
alias delevn='pkg env pop'

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

