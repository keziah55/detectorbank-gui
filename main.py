#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DetectorBank GUI.
"""
import sys
import argparse
from qtpy.QtWidgets import QApplication, QSplashScreen
from qtpy.QtGui import QPixmap

try:
    from detectorbankgui.mainwindow import DetectorBankGui
except (ImportError, ModuleNotFoundError):
    try:
        # try adding paths
        import os
        ld_lib_path = os.getenv("LD_LIBRARY_PATH", "")
        if (p:="/usr/local/lib/") not in ld_lib_path:
            os.environ["LD_LIBRARY_PATH"] = ld_lib_path + f":{p}"
        python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
        local_lib_path = os.path.join(os.path.expanduser("~"), ".local", "lib", python_version, "site-packages")
        if local_lib_path not in sys.path:
            sys.path.append(local_lib_path)
        # try to import again
        from detectorbankgui.mainwindow import DetectorBankGui
    except (ImportError, ModuleNotFoundError) as err:
        msg = ("Could not import DetectorBankGui\n "
               "Please check that both detecorbank and detectorbank-gui are installed "
               "and any environment variables (e.g. PYTHONPATH or LD_LIBRARY_PATH) "
               "are set appropriately.\n"
               f"Original error was:\n  {err}")
        raise RuntimeError(msg)

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description=__doc__)
    
    parser.add_argument('-i', '--input', help='Audio input')
    parser.add_argument('-p', '--profile', help='Profile name')

    args = parser.parse_args()

    QApplication.setApplicationName("DetectorBank")
    QApplication.setOrganizationName("SMRG")
    
    app = QApplication(sys.argv)
    
    pixmap = QPixmap("images/splash.png")
    splash = QSplashScreen(pixmap)
    splash.show()
    
    window = DetectorBankGui(audioFile=args.input, profile=args.profile)
    window.show()
    splash.finish(window)
    
    sys.exit(app.exec_())
