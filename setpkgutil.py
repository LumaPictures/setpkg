import setpkg as _setpkg

def packagedir(env, pkg, version):
    '''
    use when a package corresponds exactly with a first-level repo subdirectory
    '''
    repoRoot, version = repodir(env, pkg, version)
    return repoRoot / pkg, version

def repodir(env, pkg, version):
    '''
    the root of the user's dev repo.

    set forceto to 'server' or 'local' to force the returned path.
    '''
    if isdev(env, pkg, version):
        _setpkg.logger.debug("(pkg %s in dev mode)" % pkg)
        return env.USER_DEV, stripdev(version)
    else:
        return env.LUMA_SOFT, version

def stripdev(version):
    return version[:-4] if version.endswith('.dev') else version

def isdev(env, pkg, version):
    return (env.DEV_PACKAGES and pkg in env.DEV_PACKAGES.split()) or version.endswith('.dev')

def isDevEnv():
    return bool(os.environ.get('DEV_PACKAGES', ''))
