def packagedir(env, pkg, version):
    if isdev(env, pkg, version):
        return env.USER_DEV / pkg, stripdev(version)
    else:
        return env.LUMA_SOFT / pkg, version

def repodir(env, pkg, version):
    if isdev(env, pkg, version):
        return env.USER_DEV, stripdev(version)
    else:
        return env.LUMA_SOFT, version

def stripdev(version):
    return version[:-4] if version.endswith('.dev') else version

def isdev(env, pkg, version):
    return pkg in env.DEV_PACKAGES.split() or version.endswith('.dev')
