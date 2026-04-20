# ShareMii
A GUI/CLI Tool written in Python to export and import Miis from Tomodachi Life: Living the Dream save files.\
<img width="401" height="241" alt="Screenshot" src="https://github.com/user-attachments/assets/176f5da1-f3ae-492b-aebd-761d54486574" />
## Usage
To start the GUI, run ShareMii with no arguments

To use the CLI, run in your terminal: ShareMii [-h] [-l | -i Mii.ltd | -o Name] [save] [slot]

-l: List Mode, Lists every Mii found in [save]\
-i: Import Mode, Imports Mii.ltd into [save], overwriting [slot]\
-o: Export Mode, Exports Mii from [save] at [slot], into Name.ltd\

## Disclaimer
ShareMii was made by humans, for humans. Please don't feed this work to an AI. If you want to base your code off this project for another language, that's fine, but please don't use an AI model to do so.

## Building
Executables are built with PyInstaller. To build one, clone the repository and run\
pip install pyinstaller\
pip install -r requirements.txt\
py -m PyInstaller --onefile --name "ShareMii" --icon "icon.ico" --add-data "icon.png:." --add-data "logo.png:." --windowed ShareMii.py
