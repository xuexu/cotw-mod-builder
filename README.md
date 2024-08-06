# cotw-mod-builder

A tool that makes it easy to customize and create mods for theHunter: Call of the Wild (COTW).

Release builds are available here on GitHub and on NexusMods: https://www.nexusmods.com/thehuntercallofthewild/mods/410

![Recording](https://github-production-user-asset-6210df.s3.amazonaws.com/2107385/297992314-5f7d6c72-8754-42d0-9d4a-4b7a06912b3a.png)

## How to Build
> Note: This was built and tested with Python 3.9.6

1. Setup virtual environment:
```
python -m venv venv
venv\Scripts\activate
```
2. Install dependencies:
```shell
pip install -r requirements.txt
python -m PySimpleGUI.PySimpleGUI upgrade
```
3. Run the application:
```shell
python -m modbuilder
```

## PySimpleGUI Licensing

PySimpleGUI [changed their license terms in early 2024](https://docs.pysimplegui.com/en/latest/documentation/installing_licensing/license_keys/) to require an account to use the software. A free "hobbyist" account can be used without restrictions for development, however a paid "commercial" account is needed in order to get distribution keys that can be included in compiled binaries. If a free account is used to compile an .exe then PySimpleGUI will launch first and demand the end-user signs up for an account or activates a 30-day trial of the software, after which they will need an account. With a distribution key, the license is invisible to the end-user and there is no prompt for an account or trial activation.

For now, I am building release versions of this tool with a distribution license that I paid for. Once the 1-year license expires, I may drop that license and update this project to use [FreeSimpleGUI](https://github.com/spyoungtech/FreeSimpleGUI) instead.
