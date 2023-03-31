#!/bin/bash

GUI_DIR=$(pwd)

## install all dependencies

# detectorbank dependencies
sudo apt install python3-dev python3-numpy swig build-essential autoconf-archive pkg-config libtool libcereal-dev librapidxml-dev libfftw3-dev doxygen python3 graphviz python3-tap

# gui dependencies
sudo apt install python3-numpy python3-scipy python3-bs4 python3-pyqt5 python3-qtpy python3-pyqtgraph python3-pip
python3 -m pip install git+https://github.com/keziah55/CustomPyQtObjects.git

## install DetectorBank
cd ..
git clone https://github.com/keziah55/DetectorBank.git
cd DetectorBank
autoreconf --install --verbose
mkdir -p build
cd build
../configure
make
sudo make install

## back to gui
cd $GUI_DIR

## copy script and icon, make .desktop

# copy script to ~/.local/bin
LOCAL_BIN="/home/$USER/.local/bin"
mkdir -p $LOCAL_BIN
if [[ :$PATH: != *:"$LOCAL_BIN":* ]]; then
  export $PATH=$PATH:$LOCAL_BIN
fi
chmod 755 detectorbank-gui
cp detectorbank-gui $LOCAL_BIN

# make .desktop file
ICON_PATH=$(pwd)/images/icon.png
sed -i "/Icon=\/path\/here\/images\/icon.png/$ICON_PATH/" detectorbank-gui.desktop
cp detectorbank-gui.desktop "/home/$USER/.local/share/applications"
