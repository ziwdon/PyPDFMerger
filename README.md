
**Description**  
Simple Python app to merge multiple PDF files into a single one.

**Setup**

1. **Clone the Repository**:
   ```sh
   git clone <repository-url>
   cd PyPDFMerger
   ```

2. **Create and Activate Virtual Environment**:
   ```sh
   python -m venv myenv
   # Windows
   .\myenv\Scripts\activate
   # macOS/Linux
   source myenv/bin/activate
   ```

3. **Install Dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

4. **If using VS Code**:
   - Open the project folder in VS Code.
   - VS Code should automatically detect and use the virtual environment.
   
     If VS Code does not automatically detect the virtual environment, you can manually select it:
     - Open the command palette (`Ctrl+Shift+P` or `Cmd+Shift+P` on macOS).
     - Type `Python: Select Interpreter` and select the interpreter located in your virtual environment (`./myenv/Scripts/python` for Windows or `./myenv/bin/python` for macOS/Linux).

**Usage**  
Debug the project, or generate an executable file and run the PyPDFMergerGUI.exe in the build folder.

- **To generate an executable file**:
  ```sh
  pip install cx-Freeze
  python setup.py build
  ```
