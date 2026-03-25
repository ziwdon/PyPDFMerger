from cx_Freeze import setup, Executable

build_exe_options = {
    "excludes": ["test", "unittest"],
}

setup(
    name="PyPDFMerger",
    version="1.0",
    description="A PDF Merger GUI",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "PyPDFMerger/PyPDFMergerGUI.pyw",
            base="Win32GUI",
            target_name="PyPDFMerger",
        )
    ],
)
