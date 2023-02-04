# Installation

You'll need to install the [DetectorBank](https://github.com/keziah55/DetectorBank), 
then download the [GUI](https://github.com/keziah55/detectorbank-gui) and its requirements. 
You'll also need a Qt5 or Qt6 installation, along with
corresponding Python bindings, either PyQt or PySide (NB PySide2, as installed from PyPI, does not 
work with Python 3.11. However, if you install PySide2 from your system repositories, it may work).

## Installing DetectorBank

Follow the instructions [here](https://github.com/keziah55/DetectorBank#requirements) to install
DetectorBank on your system. 

## Installing other requirements

First clone the detectorbank-gui repository to a suitable location
```
git clone https://github.com/keziah55/detectorbank-gui.git
```

You can install the requirements with pip:
```
cd detectorbank-gui
python -m pip install -r requirements.txt
```
Note that this will install PyQt5, PyQt6, PySide2 and PySide6.

Alternatively, on Debian/Ubuntu install:
```
apt install python3-numpy python3-scipy python3-bs4 python3-lxml python3-qtpy python3-pyqtgraph
```
along with the PyQt/PySide package of your choice, and 
```
python -m pip install git+https://github.com/keziah55/CustomPyQtObjects.git
```

## Make executable and desktop files

You may wish to create a script in your `PATH` to launch the GUI, e.g.
```
#!/bin/bash

python /path/to/detectorbank-gui/main.py "$@"
```

The git repo conatins a [.desktop file](https://github.com/keziah55/detectorbank-gui/blob/main/detectorbank-gui.desktop). 
If you want DetectorBank GUI to appear in your application launcher, 
you can copy this to a suitable location, e.g. ~/.local/share/applications/ and change the entry
for `Exec` to the path to the above script and `Icon` to detectorbank-gui/images/icon.png.
