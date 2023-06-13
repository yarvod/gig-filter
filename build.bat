pyInstaller main.py -n YIG_filter_manager --onedir --noconsole --icon=.\assets\logo.png -y
copy calibration.csv .\dist\YIG_filter_manager\calibration.csv
mkdir .\dist\YIG_filter_manager\assets
copy .\assets\* .\dist\YIG_filter_manager\assets