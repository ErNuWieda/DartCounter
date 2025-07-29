import os
import sys

# --- One-time setup for all tests, executed by pytest before test collection ---

# Workaround for TclError on Windows in venv
# In some environments (like Windows virtualenvs), the Python interpreter
# can't find the Tcl/Tk libraries. This block manually sets the
# environment variables to point to the correct location within the
# Python installation directory before any Tkinter modules are imported.
if sys.platform == "win32":  # "win32" is the value for both 32-bit and 64-bit Windows
    # In a venv, sys.prefix points to the venv dir, but the Tcl/Tk libs are
    # in the base Python installation. sys.base_prefix correctly points there.
    tcl_dir = os.path.join(sys.base_prefix, 'tcl')
    if os.path.isdir(tcl_dir):
        # Find the specific tcl8.x and tk8.x directories
        for d in os.listdir(tcl_dir):
            lib_path = os.path.join(tcl_dir, d)
            if os.path.isdir(lib_path):
                if d.startswith('tcl8.') and "TCL_LIBRARY" not in os.environ:
                    os.environ['TCL_LIBRARY'] = lib_path
                elif d.startswith('tk8.') and "TK_LIBRARY" not in os.environ:
                    os.environ['TK_LIBRARY'] = lib_path