# PyPDFMerger

A simple GUI application for merging multiple PDF files into one or splitting a PDF into multiple outputs, built with Python and tkinter.

## Features

- Merge mode:
  - Select and merge multiple PDF files into a single PDF
  - Reorder files before merging with Move Up / Move Down
  - Remove individual files from the selection
  - Automatic validation — invalid or unreadable PDFs are skipped with a warning
- Split mode:
  - Split one PDF by page ranges (for example: `1-3,5,8-10`)
  - Split one PDF every N pages
  - Split one PDF by top-level bookmarks/sections
- English / Spanish language toggle

## Requirements

- Python 3.8 or later
- Dependencies listed in `requirements.txt` (`pypdf`, `cx_Freeze`)

## Setup

1. **Clone the repository**:
   ```sh
   git clone <repository-url>
   cd PyPDFMerger
   ```

2. **Create and activate a virtual environment**:
   ```sh
   python -m venv myenv
   # Windows
   .\myenv\Scripts\activate
   # macOS/Linux
   source myenv/bin/activate
   ```

3. **Install dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

### Run directly

```sh
python PyPDFMerger/PyPDFMergerGUI.pyw
```

> On Windows you can also double-click the `.pyw` file to launch the app without a console window.

### Build a standalone executable (Windows only)

```sh
python setup.py build
```

The executable `PyPDFMerger.exe` will be placed inside the generated `build/` folder.

## VS Code

Open the project folder in VS Code. VS Code should automatically detect and activate the virtual environment.

If it does not, select the interpreter manually:

- Open the command palette (`Ctrl+Shift+P`, or `Cmd+Shift+P` on macOS).
- Choose **Python: Select Interpreter** and pick the interpreter inside your virtual environment (`./myenv/Scripts/python` on Windows or `./myenv/bin/python` on macOS/Linux).
