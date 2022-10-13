#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog to edit detector frequencies and bandwidths
"""

from qtpy.QtWidgets import QDialog

class FrequencyWidget(QDialog):
    def __init__(self, *args, defaultFreqs=[], defaultBws=[], **kwargs):
        super().__init__(*args, **kwargs)