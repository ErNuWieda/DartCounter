import os
import sys
import logging

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

def pytest_configure(config):
    """
    Konfiguriert das Logging für die Test-Suite, um die Konsolenausgabe zu unterdrücken.

    Diese Funktion wird von pytest automatisch vor der Testausführung aufgerufen.
    """
    # Hole den Root-Logger, auf dem die Handler in `logger_setup.py` konfiguriert werden.
    root_logger = logging.getLogger()

    # Entferne alle existierenden Handler, um eine saubere Konfiguration zu gewährleisten.
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Füge einen NullHandler hinzu. Dieser "schluckt" alle Log-Nachrichten,
    # ohne sie auszugeben. Dies verhindert, dass Anwendungs-Logs die Testausgabe stören.
    root_logger.addHandler(logging.NullHandler())