#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DetectorBank GUI.
"""
import sys
import argparse
from qtpy.QtWidgets import QApplication
from src.main import DBGui

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description=__doc__)
    
    parser.add_argument('-i', '--input', help='Audio input')
    parser.add_argument('-p', '--profile', help='Profile name')

    args = parser.parse_args()

    QApplication.setApplicationName("DetectorBank")
    QApplication.setOrganizationName("SMRG")
    
    app = QApplication(sys.argv)
    
    window = DBGui(audioFile=args.input, profile=args.profile)
    window.show()
    
    sys.exit(app.exec_())
