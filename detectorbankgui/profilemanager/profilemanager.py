#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ProfileManager object to return extant profile and save new ones.
"""

from bs4 import BeautifulSoup
import numpy as np
from pathlib import Path

class Profile:
    lookup = {"numThreads":"maxThreads", "damping":"d"}
    def __init__(self, profile):
        self.p = profile

    def _getNumber(self, name, numType=float):
        """ Given bs4 element of profile, return value of `name` as `numType` """
        return numType(self.p.find(name).text)
        
    def _parseFeatures(self):
        """ Return text of method, frequency normalisation and amplitude normalisation to be sent to combobox """
        d = {"Runge-Kutta method":"Fourth order Runge-Kutta",
             "Central difference method":"Central difference",
             "Frequency unnormalized":"Unnormalized",
             "Search-normalized":"Search normalized",
             "Amplitude unnormalized":"Unnormalized",
             "Amplitude normalized":"Normalized"}
        featuresStr = self.p.find("featureSet").text
        features = [d.get(feature, feature) for feature in featuresStr.split(',')]
        return features
    
    def _parseFreqsBws(self):
        """ Given bs4 element of profile, return list of frequencies and list of bandwidths """
        size = int(self.p.find("numDetectors").text)
        freqs = np.zeros(size)
        bws = np.zeros(size)
        detectors = self.p.find_all("Detector")
        for n, detector in enumerate(detectors):
            freqs[n] = float(detector.w_in.text) / (2*np.pi)
            bws[n] = float(detector.bw.text)
        return np.column_stack((freqs, bws))
    
    def value(self, valueName):
        """ Get value from profile, cast to correct data type """
        valueName = self.lookup.get(valueName, valueName)
        if valueName == "features":
            return self._parseFeatures()
        elif valueName in ["sr", "d", "gain"]:
            return self._getNumber(valueName)
        elif valueName == "maxThreads":
            return self._getNumber(valueName, int)
        elif valueName == "detChars":
            return self._parseFreqsBws()
        else:
            return None

class ProfileManager:
    def __init__(self, configfile=None):
        self._configfile = configfile if configfile is not None else Path.home().joinpath(".config", "hopfskipjump.xml")
        if not self._configfile.exists():
            with open(self._configfile, "w") as fileobj:
                fileobj.write("")
                
    @property
    def soup(self):
        with open(self._configfile) as fileobj:
            soup = BeautifulSoup(fileobj, "xml")
        return soup
                
    @property
    def profiles(self):
        return [p['name'] for p in self.soup.find_all("profile")]
    
    def getProfile(self, name):
        p = self.soup.find("profile", attrs={'name':name})
        if p is not None:
            return Profile(p)
        else:
            return None