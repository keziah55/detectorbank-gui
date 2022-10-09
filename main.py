#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run DetectorBank GUI.
"""
import sys
from qtpy.QtWidgets import QApplication
from src.main import DBGui

if __name__ == '__main__':

    QApplication.setApplicationName("DetectorBank")
    QApplication.setOrganizationName("SMRG")
    
    app = QApplication(sys.argv)
    
    window = DBGui()
    window.show()
    
    sys.exit(app.exec_())
