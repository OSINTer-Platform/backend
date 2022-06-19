from os.path import dirname, basename, isfile, join
import glob

modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [
    basename(f)[:-3] for f in modules if isfile(f) and not basename(f).startswith("__")
]

from modules import config, misc

misc.createFolder("logs")

configOptions = config.backendConfig()
