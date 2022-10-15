#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 19:16:45 2022

@author: keziah
"""
from qtpy.QtWidgets import QLabel, QSpinBox, QDoubleSpinBox
from qtpy.QtCore import Qt
from .abstractpage import AbstractPage
import numpy as np

class BandwidthPage(AbstractPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, name="bandiwdth", **kwargs)