#! /bin/bash

pyInstaller main.py -n YIG_filter_manager --onedir --icon="./assets/logo.png" --add-data "./assets:./assets" --add-data "./calibration.csv:." --noconsole --windowed -y
