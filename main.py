#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DetectorBank GUI.
"""

try:
    from detectorbankgui.mainwindow import DetectorBankGui
except (ImportError, ModuleNotFoundError):
    try:
        import os, sys
        from pathlib import Path
        if sys.argv[-1] == "stop now please":
            # we've already tried this once, don't keep looping
            raise Exception
            
        # try adding paths
        ld_lib_path = os.getenv("LD_LIBRARY_PATH", "")
        if (p:="/usr/local/lib/") not in ld_lib_path:
            os.environ["LD_LIBRARY_PATH"] = ld_lib_path + f":{p}"
        python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
        local_lib_path = str(Path.home().joinpath(".local", "lib", python_version, "site-packages"))
        if local_lib_path not in sys.path:
            sys.path.append(local_lib_path)
            
        # try again
        # append message to argv so we don't loop infinitely
        argv = sys.argv + ["stop now please"]
        os.execv(sys.argv[0], argv)
    except Exception as err:
        msg = ("Could not import DetectorBankGui\n "
                "Please check that both detecorbank and detectorbank-gui are installed "
                "and any environment variables (e.g. PYTHONPATH or LD_LIBRARY_PATH) "
                "are set appropriately.")
        raise RuntimeError(msg)
        
import sys
import os
from pathlib import Path
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
    possible_paths = [
        Path("images", "splash.png"),
        Path.home().joinpath(".local", "share", "detectorbank-gui", "splash.png")
    ]
    for p in possible_paths:
        if p.is_file():
            splash_path = p
            break
    if splash_path is not None:
        pixmap = QPixmap(str(splash_path))
        splash = QSplashScreen(pixmap)
        splash.show()
    
    window = DetectorBankGui(audioFile=args.input, profile=args.profile)
    window.show()
    
    if splash_path is not None:
        splash.finish(window)
    
    sys.exit(app.exec_())
