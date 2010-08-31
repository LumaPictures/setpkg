import setpkg as _setpkg

def packagedir(env, pkg, version):
    repoRoot, version = repodir(env, pkg, version)
    return repoRoot / pkg, version

def repodir(env, pkg, version):
    if isdev(env, pkg, version):
        _setpkg.logger.debug("(pkg %s in dev mode)" % pkg)
        return env.USER_DEV, stripdev(version)
    else:
        return env.LUMA_SOFT, version

def stripdev(version):
    return version[:-4] if version.endswith('.dev') else version

def isdev(env, pkg, version):
    return pkg in env.DEV_PACKAGES.split() or version.endswith('.dev')

def isDevEnv():
    return bool(os.environ.get('DEV_PACKAGES', ''))
