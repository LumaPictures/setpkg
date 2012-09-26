import setpkg as _setpkg
import os
import platform as _platform

DEV_VERSION_SUFFIX = '.dev'

def packagedir(env, pkg, version):
    '''
    use when a package corresponds exactly with a first-level repo subdirectory
    '''
    repoRoot, version = repodir(env, version)
    return os.path.join(repoRoot, pkg), version

# Transition code - once this new setpkgutil is puppeted out, can change all
# pykg files to use two-arg version of repodir, and rename repodir_new to
# repodir
def repodir_new(env, version):
    '''
    the root of the user's dev repo.
    '''
    if _setpkg.Session.current_version('pipe') is not None or 'REPO_PATH' in env:
        repodir = env.REPO_PATH.value()
    else:
        repodir = env.LUMA_SOFT.value()
    return repodir, stripdev(version)

def isdev(envOrVersion, pkg=None, version=None):
    # Don't need env or pkg, but decided to leave them in, in case they are
    # needed later (and because didn't want to deal with puppet transition
    # issues)
    if version is None:
        version = envOrVersion
    return version.endswith(DEV_VERSION_SUFFIX)

def repodir(env, pkgOrVersion, version=None):
    '''
    the root of the user's dev repo.
    '''
    if version is None:
        version = pkgOrVersion
    return repodir_new(env, version)

def stripdev(version):
    return version[:-len(DEV_VERSION_SUFFIX)] if isdev(version) else version

def anydev():
    return bool(os.environ.get('DEV_PACKAGES', ''))

def isDevRepo():
    return bool(os.environ.get('DEV_REPO', ''))

def mayaModule(env, moduleDir):
    """
    expands standard maya environment variables based on a root module directory
    """
    if _platform.system() == 'Darwin':
        env.XBMLANGPATH += moduleDir + '/icons'
    else:
        env.XBMLANGPATH += moduleDir + '/icons/%B'

    env.MAYA_PRESET_PATH += moduleDir + '/presets'
    env.MAYA_SCRIPT_PATH += moduleDir + '/scripts'
    env.MAYA_PLUG_IN_PATH += moduleDir + '/plug-ins'
    env.MAYA_SHELF_PATH += moduleDir + '/shelves'
    env.PYTHONPATH += moduleDir + '/scripts'
    env.PYTHONPATH += moduleDir + '/python'
