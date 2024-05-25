from cx_Freeze import setup, Executable

setup(
    name = "PyPDFMerger",
    version = "1.0",
    description = "A PDF Merger GUI",
    executables = [Executable("PyPDFMerger/PyPDFMergerGUI.pyw", base="Win32GUI")]
)
