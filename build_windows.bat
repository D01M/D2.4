@echo off
pyinstaller --onefile --noconsole --name OpenSeismo --add-data "openseismo\templates;openseismo\templates" --add-data "openseismo\static;openseismo\static" app_launcher.py