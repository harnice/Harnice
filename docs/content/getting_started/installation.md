***********
1. Install Homebrew (if not already):
   https://brew.sh/

2. Install git using Homebrew (not the .pkg installer):
   brew install git

3. Configure your GitHub authentication:
   brew install gh
   gh auth login
   (choose GitHub.com → HTTPS → “Login with browser”)

4. Clone the repo:
   git clone https://github.com/harnice/Harnice.git

***********
1. Update library_locations.csv to point Harnice towards your libararies. Make the file if it doesn't exist in the root of your harnice repo.
    here's the header row:
    :
        repo_url,local_path
    :

    here's an example:
    :
        repo_url,local_path
        https://github.com/harnice/harnice-library-public,Users/kenyonshutt/Documents/github/harnice-library-public
    :
    add whatever other library you need in this document. pull components from that library by referencing them by their url for traceability purposes. 
    you can use git or dropbox or whatever to control your libraries in a repo separate from harnice, as you wish.
    local_path is used to point harnice towards where the files for that repo live on your computer, but is not stored in any part definition.

*************
2. install python however you want

*************
3. install the following packages:

    Option A: Install via pip (recommended):
        pip install -e .
    
    Option B: Manual installation:
        # Core dependencies:
        pip install PySide6>=6.6
        pip install sexpdata
        pip install Pillow
        pip install PyYAML
        
        # Macro dependencies (used by library macros):
        pip install xlwt
        pip install lxml
        pip install PyPDF2
        
    System dependencies:
        brew install poppler  # for pdfunite

***********
4. make sure you have real apps installed that interface with files that Harnice reads and writes:
    text editor to edit feature trees (VSCode, Cursor, Xcode, notepad++, etc)
    SVG editor (Inkscape preferred)
    TSV editor (Excel preferred)
    Kicad