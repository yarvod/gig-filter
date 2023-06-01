#! /bin/bash

pyInstaller main.py -n YIG_filter_manager --onedir -y
cp calibration.csv ./dist/YIG_filter_manager/calibration.csv