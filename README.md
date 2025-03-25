# Mod Builder - Revived

A tool that makes it easy to customize and create mods for theHunter: Call of the Wild (COTW).

Release builds are available here on GitHub and on NexusMods: https://www.nexusmods.com/thehuntercallofthewild/mods/410

> Enable mods by adding the following launch options to your game executable: `--vfs-fs dropzone --vfs-archive archives_win64 --vfs-archive patch_win64 --vfs-archive dlc_win64 --vfs-fs .`

![Screenshot](screenshot.png)

# Updating Mod Builder Files

After each game update to theHunter: Call of the Wild, Mod Builder needs to be updated with the latest game files. While I perform this process for each new release, the files can also be updated manually by an end-user.

> **NOTE:** Depending on the scope of changes from a game update, some mods may require code updates to continue working properly. Patching updated files into an older Mod Builder version not built for those files may result in bugs/crashes.

1. Download the latest release of [DECA](https://github.com/kk49/deca/releases)
1. Use DECA to unpack `theHunterCotW_F.exe`
1. Look in the `/modbuilder/org` folder to determine which files to extract with DECA
1. Use the "Extract Raw Files" option to extract each new file (extracting whole folders may be faster than checking every file)
1. Copy the extracted folders from the `/work/hp/extracted` folder where you installed DECA
1. Paste the new files into `/modbuilder/org` and overwrite any changed files

## How to Add New Item Names

Internal item names from the game files are mapped to human-readable names in `name_map.yaml`. This file can be found in the `_internal` folder of an already-built Mod Builder release to update an existing version. When new items are added to the game they will appear as `equipment_<type>_<name>_01` in mods like Modify Ammo, Modify Store, and Modify Weapon. Adding the appropriate data to `name_map.yaml` will allow all of the mods to display a proper name.

1. Determine the "internal" name of the item by reading the name parsed and displayed by Mod Builder from Modify Store (reads from `equipment_data.bin`)
1. Open `name_map.yaml` in a text editor
1. Find the appropriate location to add the equipment. Ammos/Sights/Weapons/Lures are organized by type. Try to keep things mostly alphabetical
1. Add the item name as a new key, removing the `equipment_<type>_` prefix. Variant suffixes (`_01`, `_02`) should be removed to group reskins of the same item (common for weapons and structures).
1. Fill in relevant data for the value (name, type, variant info)

Modify Weapon pulls names from `.wtunec` tuning files in `org/editor/entities/hp_weapons`. These names often do not match the names from other locations. Some weapons have multiple tuning files for different ammos (shotguns with shot/slugs, Grelck Drilling Rifle, etc). Most of these are handled as duplicate entries using YAML anchors (`&item` and `*item`), with an optional `ammo` value to differentiate mutliple tuning files. Follow the examples in the file to see how to format new additions.

## How to Build

> **NOTE:** This was built and tested with Python 3.12.8

1. Setup virtual environment:
```
python -m venv venv
venv\Scripts\activate
```
2. Install dependencies:
```shell
pip install -r requirements.txt
```
3. Run the application:
```shell
python -m modbuilder
```
4. Build the application. The `.exe` and accompanying `_internal` folder will be placed in `\build`
```shell
pip install pyinstaller
.\scripts\build.bat
```
5. Pack the application. The `modbuilder.7z` file will be placed in `\dist`
```shell
.\scripts\pack.bat
```
6. Alternatively, build + pack the application with an automated version number tag from `setup.cfg` (eg. `modbuilder_2.2.4.7z`)
```shell
.\scripts\build.bat && .\scripts\version.bat
```
