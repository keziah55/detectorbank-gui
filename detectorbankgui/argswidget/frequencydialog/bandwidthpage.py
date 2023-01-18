#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 19:16:45 2022

@author: keziah
"""
from customQObjects.widgets import DoubleSpinBox
from .abstractpage import AbstractPage, RightLabel

class BandwidthPage(AbstractPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, name="bandwidth", **kwargs)
        
        label = RightLabel("Bandwidth:")
        self.box = DoubleSpinBox()
        self.box.setMaximum()
        self.box.setSuffix(" Hz")
        
        row = 0
        self.layout.addWidget(label, row, 0)
        self.layout.addWidget(self.box, row, 1)
        row += 1
        self.layout.addWidget(self.doneButton, row, 0, 1, 2)
        row += 1
        self.layout.setRowStretch(row, 10)
        
    @property
    def value(self) -> float:
        """ Return bandwidth """
        return self.box.value()
        