

tree3d was developed using Python 3.6.

Version 1.0 was Jonas Hurst's bachelor thesis project

## Instructions on how to build tree3d

* clone repository from gitlab to local hard drive
* spatialite:
    * download libspatialite (developed using MS Windows Binaries NEXT GENERATION x64)
    * http://www.gaia-gis.it/gaia-sins/
    * unpack archive, add all files to the project's /src/ directory
* cyqlite
    * Download cyqlite
    * https://sourceforge.net/projects/cyqlite/files/
    * add sqlite3.dll to Python36/DLLs/
    * Overwrite existing sqlite3.dll file (or rename it)
* Install Python packages
    * lxml
    * PyInstaller
    * pyproj
    * requests
    * wxPython
* build
    * Open command prompt
    * navigate to projct's /buiild/ folder
    * execute command
    * `pyinstaller --onefile --windowed --icon=icon.ico .\..\src\tree3d.py`
* Place /build/dist/tree3d.exe in a new directory
    * Add /src/citygml_vegetation_codes.code file to this directory
    * Add SpatiaLite files to this directory

