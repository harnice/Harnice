# Installation

---

## :octicons-download-16: Quick install Harnice

Install Harnice directly from PyPI:

```bash
pip install harnice
```

*if you need help with this, check out [this guide](https://packaging.python.org/en/latest/tutorials/installing-packages/) about how to install packages, or python in the first place*

...or...

## :material-keyboard-outline: Development installation (*for contributing*)

This approach is recommended because it would be great if you could contribute to adding your parts to the public library! Of course, you don't have to.

### 1. Clone the Repository

```bash
git clone https://github.com/harnice/Harnice.git
cd Harnice
```

**Note:** If you're on macOS, ensure you have Homebrew and git installed:
```bash
brew install git
brew install gh
gh auth login
```
*if you need help with this, check out [the official git website](https://git-scm.com/book/en/v2), make an account on github, gitlab, or similar, and consult the many available youtube resources*

### 2. Install Dependencies

Install Harnice in editable mode:

```bash
pip install -e .
```

Or install dependencies manually:

```bash
# Core dependencies
pip install PySide6>=6.6 sexpdata Pillow PyYAML xlwt webcolors

# System dependencies (macOS)
brew install poppler  # for pdfunite
```

---

## :octicons-arrow-switch-16: Configure Library Paths

Create `library_locations.csv` in the root of your Harnice repository if it doesn't exist. Populate it with the following content: 

```csv
repo_url,local_path
https://github.com/harnice/harnice,/Users/kenyonshutt/Documents/GitHub/harnice/library_public
```

![Library locations example](images/installation_images/library_locations.png)

Add entries for any external libraries you want to use. The `local_path` points to where the library files live on your computer, but the repo_url should be traceable by your collaborators.

This isn't included in the installation process because each user will have a different local path, and thus it must be ignored by git. 

---

## :material-mouse-variant: Install Supporting Applications

Make sure you have these applications installed for working with Harnice files:

- **Code editor** - For editing feature trees ([VSCode](https://code.visualstudio.com/), [Cursor](https://cursor.com/), Notepad++, etc.)
- **SVG editor** - Designed to work with [Inkscape](https://inkscape.org/)
- **CSV editor** - Excel or similar spreadsheet application
- [**KiCad**](https://www.kicad.org/) - For drawing block diagrams
