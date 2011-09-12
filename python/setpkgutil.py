import setpkg as _setpkg
import os

def packagedir(env, pkg, version):
    '''
    use when a package corresponds exactly with a first-level repo subdirectory
    '''
#    repoRoot, version = repodir(env, pkg, version)
#    return os.path.join(repoRoot, pkg), version
    return os.path.join(env.REPO_PATH.value(), pkg), version

def repodir(env, pkg, version):
    '''
    the root of the user's dev repo.
    '''
    if isdev(env, pkg, version):
        _setpkg.logger.debug("(pkg %s in dev mode)" % pkg)
        ver = stripdev(version)
        repodir = env.USER_DEV.value()
        if repodir is None:
            dev_root = env.DEV_ROOT.value()
            if dev_root is None:
                dev_root = env.LUMA_SOFT / 'dev'
            repodir = os.path.join(dev_root, env.USER.value())
    else:
        if env.USE_SVDEV:
            repodir, ver = env.REPO_PATH.value(), version
        else:
            repodir, ver = env.LUMA_SOFT.value(), version
    return repodir, ver

def stripdev(version):
    return version[:-4] if version.endswith('.dev') else version

def isdev(env, pkg, version):
    return (env.DEV_PACKAGES and pkg in env.DEV_PACKAGES.split()) or version.endswith('.dev')

def anydev():
    return bool(os.environ.get('DEV_PACKAGES', ''))
