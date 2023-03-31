# DetectorBank GUI

A simple app to use [DetectorBank](https://github.com/keziah55/DetectorBank) 
to visualise and analyse audio.

See the [User guide](https://keziah55.github.io/detectorbank-gui/user_guide/)
for an overview of the application.

## Requirements

- [DetectorBank](https://github.com/keziah55/DetectorBank)
- [numpy](https://numpy.org/)
- [scipy](https://docs.scipy.org/doc/scipy/index.html) or [soundfile](https://pypi.org/project/soundfile/)
- [pyqtgraph](https://pyqtgraph.readthedocs.io/en/latest/index.html)
- [qtpy](https://pypi.org/project/QtPy/)
- [pyqt5](https://www.riverbankcomputing.com/software/pyqt/) or [pyside2](https://wiki.qt.io/Qt_for_Python)
- [customQObjects](https://github.com/keziah55/CustomPyQtObjects)
- [BeautifulSoup](https://pypi.org/project/beautifulsoup4/)
- lxml

To build the documentation:

- [mkdocs](https://www.mkdocs.org/)
- [pymdown-extensions](https://facelessuser.github.io/pymdown-extensions/)

To run the tests:

- pytest
- pytest-qt
- pytest-cov 
- pytest-profiling 

## Installation

The provided `install.sh` script installs the dependencies 
and add to your system's application launcher
```
./install.sh
```
Note that on Debian/Ubuntu, this install PyQt5, but on Fedora it installs PySide2.

If you already have [DetectorBank](https://github.com/keziah55/DetectorBank) and its dependencies installed,
don't install again:
```
./install.sh --no-install-detectorbank
```
