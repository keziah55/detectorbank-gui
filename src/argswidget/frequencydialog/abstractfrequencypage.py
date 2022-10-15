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

class AbstractFrequencyPage(QWidget):
    valid = Signal(bool)
    
    frequencies = Signal(object)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.doneButton = QPushButton("Set frequencies")
        self.doneButton.clicked.connect(self._emitFrequencies)
        
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
    
    def _emitFrequencies(self):
        self.frequencies.emit(self.value)