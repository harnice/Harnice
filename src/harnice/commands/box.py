import os
import json
from harnice import fileio
import runpy

def render():
    if not os.path.exists(fileio.path("signals list instructions")):
        pass #make a new signals list instructions file
        
    runpy.run_path(fileio.path("signals list instructions"))