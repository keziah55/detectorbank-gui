# Installation

This app is distributed with an [install](https://github.com/keziah55/detectorbank-gui#installation) script that
will install all dependencies and add the app to your application launcher. (NB on Debian/Ubuntu systems, this 
installs PyQt5; on Fedora it install PySide2)

## Manual installation

To install manually, first install the [DetectorBank](https://github.com/keziah55/DetectorBank), 
then download the [GUI](https://github.com/keziah55/detectorbank-gui) and its requirements. 
You'll also need a Qt5 or Qt6 installation, along with
corresponding Python bindings, either PyQt or PySide (NB PySide2, as installed from PyPI, does not 
work with Python 3.11. However, if you install PySide2 from your system repositories, it may work).

### Installing DetectorBank

Follow the instructions [here](https://github.com/keziah55/DetectorBank#requirements) to install
DetectorBank on your system. 

### Installing other requirements

First clone the detectorbank-gui repository to a suitable location
```
git clone https://github.com/keziah55/detectorbank-gui.git
```

You can install the requirements with pip:
```
cd detectorbank-gui
python -m pip install -r requirements.txt
```
Note that this will install PyQt5.

Alternatively, on Debian/Ubuntu install:
```
apt install python3-numpy python3-scipy python3-bs4 python3-qtpy python3-pyqtgraph
```
or Fedora:
```
dnf install python3-numpy python3-scipy python3-beautifulsoup4 python3-QtPy python3-pyqtgraph
```
along with the PyQt/PySide package of your choice, and 
```
python -m pip install git+https://github.com/keziah55/CustomPyQtObjects.git
```

### Make executable and desktop files

The detectorbank-gui source also contains a [detectorbank-gui script](https://github.com/keziah55/detectorbank-gui/blob/main/detectorbank-gui). Copy this to somewhere in your `$PATH`.

The git repo conatins a [.desktop template](https://github.com/keziah55/detectorbank-gui/blob/main/detectorbank-gui.desktop.template) file. 
If you want DetectorBank GUI to appear in your application launcher, 
you can change the entry for `Icon` to detectorbank-gui/images/icon.png 
and save this to a suitable location (without '.template'), 
e.g. ~/.local/share/applications/detectorbank-gui.desktop
