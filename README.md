# ShareMii
A GUI/CLI Tool written in Python to export and import content from Tomodachi Life: Living the Dream save files.\
<img width="401" height="241" alt="Screenshot" src="https://github.com/user-attachments/assets/176f5da1-f3ae-492b-aebd-761d54486574" />
## Usage
To start the GUI, run ShareMii with no arguments

To use the CLI, run in your terminal: ShareMii [-h] [-l | -i Mii.ltd | -o Name] [save] [slot]

-l: List Mode, Lists every Mii found in [save]\
-i: Import Mode, Imports Mii.ltd into [save], overwriting [slot]\
-o: Export Mode, Exports Mii from [save] at [slot], into Name.ltd\

## Disclaimer
ShareMii was made by humans, for humans. Please don't feed this work to an AI. If you want to base your code off this project for another language, that's fine, but please don't use an AI model to do so.

If your code directly ports how importing/exporting works from this repo, I'd appreciate it if you gave me credit for the code, but if you just code support for .ltd files, you're free to do whatever you want.

I would hold off on making code that parses .ltds at the moment. We're currently working on completely rewriting the ltd format to be more compatible with the game's libraries.\
If you're just supporting uploads of .ltds, you're fine, there won't be a release of the new format unless there's a working v3 -> v4 conversion.

This tool is built using PyInstaller, which can be flagged as malware on Windows. It's a false positive due to the way PyInstaller works, and how some malware also uses PyInstaller. The multifile download for Windows should be safe from this.

## Building
Executables are built with PyInstaller. To build one, clone the repository and run\
pip install pyinstaller\
pip install -r requirements.txt\
py -m PyInstaller --onefile --name "ShareMii" --icon "icon.ico" --add-data "icon.png:." --add-data "logo.png:." --windowed ShareMii.py
