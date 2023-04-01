#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DetectorBank GUI.
"""

try:
    from detectorbankgui.mainwindow import DetectorBankGui
except (ImportError, ModuleNotFoundError):
    try:
        # try adding paths
        import os, sys
        ld_lib_path = os.getenv("LD_LIBRARY_PATH", "")
        if (p:="/usr/local/lib/") not in ld_lib_path:
            os.environ["LD_LIBRARY_PATH"] = ld_lib_path + f":{p}"
        python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
        local_lib_path = os.path.join(os.path.expanduser("~"), ".local", "lib", python_version, "site-packages")
        if local_lib_path not in sys.path:
            sys.path.append(local_lib_path)
        # try again
        os.execv(sys.argv[0], sys.argv)
    except Exception as err:
        msg = ("Could not import DetectorBankGui\n "
               "Please check that both detecorbank and detectorbank-gui are installed "
               "and any environment variables (e.g. PYTHONPATH or LD_LIBRARY_PATH) "
               "are set appropriately.\n"
               f"Original error was:\n  {err}")
        raise RuntimeError(msg)
        
import sys
import os
import argparse
from qtpy.QtWidgets import QApplication, QSplashScreen
from qtpy.QtGui import QPixmap

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description=__doc__)
    
    parser.add_argument('-i', '--input', help='Audio input')
    parser.add_argument('-p', '--profile', help='Profile name')

    args = parser.parse_args()

    QApplication.setApplicationName("DetectorBank")
    QApplication.setOrganizationName("SMRG")
    
    app = QApplication(sys.argv)
    
    splash_path = None
    possible_paths = [os.path.join("images", "splash.png"),
                      os.path.join(os.path.expanduser("~"), ".local", "share", "detectorbankgui", "splash.png")]
    for p in possible_paths:
        if os.path.isfile(p):
            splash_path = p
            break
    if splash_path is not None:
        pixmap = QPixmap("images/splash.png")
        splash = QSplashScreen(pixmap)
        splash.show()
    
    window = DetectorBankGui(audioFile=args.input, profile=args.profile)
    window.show()
    
    if splash_path is not None:
        splash.finish(window)
    
    sys.exit(app.exec_())
