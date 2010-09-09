
bin=`dirname "$SETPKG_PATH"`/bin

function pkg { 
	eval `$bin/setpkgcli --pid $$ --shell $SHELL "$@"`
}

function setpkg { 
	pkg set "$@"
}

function unsetpkg { 
	pkg unset "$@"
}

function runpkg {
	setpkg "$@"
	eval `pkginfo --exe "$@"`
}

function addenv { 
	pkg env prepend "$@"
}
function delenv { 
	pkg env pop "$@"
}

# system aliases
pkg system-alias
