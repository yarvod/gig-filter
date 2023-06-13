#! /bin/bash

pyInstaller main.py -n YIG_filter_manager --onedir --noconsole --icon=./assets/logo.png -y
cp calibration.csv ./dist/YIG_filter_manager/calibration.csv
mkdir ./dist/YIG_filter_manager/assets
cp ./assets/* ./dist/YIG_filter_manager/assets/