#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 18:49:19 2022

@author: keziah
"""
from qtpy.QtWidgets import QGridLayout, QWidget, QPushButton
from qtpy.QtCore import Signal
import numpy as np
from abc import abstractmethod

class AbstractPage(QWidget):
    valid = Signal(bool)
    
    values = Signal(object)
    
    def __init__(self, *args, name="", **kwargs):
        super().__init__(*args, **kwargs)
        
        self.doneButton = QPushButton(f"Set {name}")
        self.doneButton.clicked.connect(self._emitValues)
        
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        
    @property
    @abstractmethod
    def isValid(self):
        """  """
        pass
    
    @property
    @abstractmethod     
    def value(self) -> np.ndarray:
        """ Return numpy array of frequencies """
        pass
    
    def _emitValues(self):
        self.values.emit(self.value)