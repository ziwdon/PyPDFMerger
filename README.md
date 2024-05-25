<b>Description</b></br>
Simple Python app to merge multiple PDF files into a single one.

</br><b>Setup</b></br>

1. <b>Clone the Repository</b>:
   <pre>
   <code>
   git clone &lt;repository-url&gt;
   cd PyPDFMerger
   </code>
   </pre>

2. <b>Create and Activate Virtual Environment</b>:
   <pre>
   <code>
   python -m venv myenv
   # Windows
   .\myenv\Scripts\activate
   # macOS/Linux
   source myenv/bin/activate
   </code>
   </pre>

3. <b>Install Dependencies</b>:
   <pre>
   <code>
   pip install -r requirements.txt
   </code>
   </pre>

4. <b>If using VS Code</b>:
   <ul>
     <li>Open the project folder in VS Code.</li>
     <li>VS Code should automatically detect and use the virtual environment.</li>
   </ul>
   </br>
     If VS Code does not automatically detect the virtual environment, you can manually select it:
     <ul>
       <li>Open the command palette (<code>Ctrl+Shift+P</code> or <code>Cmd+Shift+P</code> on macOS).</li>
       <li>Type <code>Python: Select Interpreter</code> and select the interpreter located in your virtual environment (<code>./myenv/Scripts/python</code> for Windows or <code>./myenv/bin/python</code> for macOS/Linux).</li>
     </ul>

</br><b>To create an executable file</b></br>
   <pre>
   <code>
      pip install cx-Freeze
      python setup.py build
   </code>
   </pre>

</br><b>Usage</b></br>
<ul>
   <b>Console version</b>:</br>
   Please make sure all your PDF files are in a folder named 'pdfs'.</br>
   The folder should be in the same root directory where the app is running.</br>
   You can use 'config.py' to change the default folder and the resulting PDF name.</br>
   
   </br><b>Executable version</b>:</br>
   Simply run the PyPDFMergerGUI.exe in the build folder.
</ul>
