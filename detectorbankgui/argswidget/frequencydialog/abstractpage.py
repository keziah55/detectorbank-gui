#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 18:49:19 2022

@author: keziah
"""
from qtpy.QtWidgets import QGridLayout, QWidget, QPushButton, QLabel
from qtpy.QtCore import Signal, Qt
import numpy as np
from abc import abstractmethod

class RightLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAlignment(Qt.AlignCenter)
        
class AbstractPage(QWidget):
    """ Base class for 'page' frequency/bandwidth widgets in FrequencyDialog """
    
    valid = Signal(bool)
    """ **signal** valid(bool `valid`) 
    
        Emitted when data validity changes
    """
    
    values = Signal(object)
    """ **signal** values(`value`)
    
        Emitted with current value (array of frequencies or bandwidth float)
        when button clicked.
    """
    
    def __init__(self, *args, name="", **kwargs):
        super().__init__(*args, **kwargs)
        
        self.doneButton = QPushButton(f"Set {name}")
        self.doneButton.clicked.connect(self._emitValues)
        
        self.valid.connect(self.doneButton.setEnabled)
        
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