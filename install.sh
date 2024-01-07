#!/bin/bash -xe

sudo echo -n

TOP_DIR=$(pwd)
PYTHON_VERSION=`python3 -c "import sys; print(f'python{sys.version_info.major}.{sys.version_info.minor}')"`
# paths where detectorbank-gui stuff will be installed
LOCAL_DIR="/home/$USER/.local"
LOCAL_INSTALL_DIR="$LOCAL_DIR/lib/$PYTHON_VERSION/site-packages"
LOCAL_BIN="$LOCAL_DIR/bin"
LOCAL_SHARE="$LOCAL_DIR/share"
LOCAL_SHARE_APPS="$LOCAL_DIR/share/applications"
# ensure these paths all exist
mkdir -p $LOCAL_INSTALL_DIR
mkdir -p $LOCAL_BIN
mkdir -p $LOCAL_SHARE_APPS

if [ -f /etc/os-release ]; then
  . /etc/os-release
else
  echo "OS $NAME not supported."
  exit 1
fi

if [[ $NAME == *"Debian"* || $NAME == *"Ubuntu"* || $NAME == *"Mint"*  ]]; then
  OS="debian"
elif [[ $NAME == *"Fedora"* ]]; then
  OS="fedora"
else
  echo "OS $NAME not supported."
  exit 1
fi

if [[ "$1" != "--no-install-detectorbank" ]]; then
  INSTALL_DETBANK=true
  
  # check if DetectorBank already exists
  if [[ -d "../DetectorBank" ]]; then
    read -p "../DetectorBank already exists. Do you want to remove it and re-install? [Y/n/c] " answer
      if [[ -z $answer ]] || [[ $answer != "${answer#[Yy]}" ]]; then 
        rm -rf "../DetectorBank"
      elif [[ $answer != "${answer#[Nn]}" ]]; then
        INSTALL_DETBANK=false
      else
        # cancel
        exit 1
    fi 
  fi
  
  if [ "$INSTALL_DETBANK" = true ]; then
    # install dependencies
    if [[ $OS == "debian" ]]; then
      sudo apt install python3-dev python3-build python3-numpy swig build-essential autoconf-archive pkg-config libtool libcereal-dev librapidxml-dev libfftw3-dev doxygen python3 graphviz python3-tap
    else
      sudo dnf install make automake gcc gcc-c++ kernel-devel python3-devel python3-build python3-numpy swig autoconf-archive libtool fftw-devel rapidxml-devel cereal-devel doxygen python3 graphviz
    fi

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
    WHEEL=`ls dist | grep \.whl`
    python3 -m pip install $WHEEL

    ## back to gui
    cd $TOP_DIR
  fi
fi
  
# gui dependencies
if [[ $OS == "debian" ]]; then
  sudo apt install python3-numpy python3-scipy python3-bs4 python3-pyqt5 python3-qtpy python3-pyqtgraph python3-pip
else
  sudo dnf install python3-numpy python3-scipy python3-beautifulsoup4 python3-pyside2 python3-QtPy python3-pyqtgraph python3-pip
fi

if [[ $NAME == *"Debian"* ]]; then
  # 'python3 -m pip install' raises an error on debian, so get it manually
  # no new dependencies to install
  mkdir -p deps
  cd deps
  if [[ -e "CustomPyQtObjects" ]]; then
    rm -rf "CustomPyQtObjects"
  fi
  if [[ -e "$LOCAL_INSTALL_DIR/customQObjects" ]]; then
    rm -rf "$LOCAL_INSTALL_DIR/customQObjects"
  fi
  git clone https://github.com/keziah55/CustomPyQtObjects.git
  cp -r $(pwd)/CustomPyQtObjects/customQObjects $LOCAL_INSTALL_DIR
  cd ..
else
  python3 -m pip install git+https://github.com/keziah55/CustomPyQtObjects.git
fi

# copy detectorbank-gui source to .local/lib
if [[ -e "$LOCAL_INSTALL_DIR/detectorbankgui" ]]; then
    rm -rf "$LOCAL_INSTALL_DIR/detectorbankgui"
fi
cp -r "$TOP_DIR/detectorbankgui" $LOCAL_INSTALL_DIR

# copy script to ~/.local/bin
if [[ -f "$LOCAL_BIN/detectorbank-gui" ]]; then
  rm "$LOCAL_BIN/detectorbank-gui"
fi
cp "$TOP_DIR/main.py" $LOCAL_BIN/detectorbank-gui

# make .desktop file
cp detectorbank-gui.desktop.template detectorbank-gui.desktop
IMG_DIR="$LOCAL_SHARE/detectorbank-gui"
mkdir -p $IMG_DIR
ICON_PATH="$IMG_DIR/icon.png"
cp "$TOP_DIR/images/icon.png" $ICON_PATH
cp "$TOP_DIR/images/splash.png" "$IMG_DIR/splash.png"
sed -i "s|/path/here/images/icon.png|${ICON_PATH}|g" detectorbank-gui.desktop
mv detectorbank-gui.desktop $LOCAL_SHARE_APPS

if [[ :$PATH: != *:"$LOCAL_BIN":* ]]; then
  msg="You may need to add \"$LOCAL_BIN\" to your PATH in order to run detectorbank-gui"
else
  msg=""
fi
printf "\nInstallation successful!\n$msg\n"
