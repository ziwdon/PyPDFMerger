"""PyPDFMerger – A simple GUI application for merging PDF files."""

from __future__ import annotations

from pathlib import Path

import pypdf
import tkinter as tk
from tkinter import filedialog, messagebox


# ── PDF logic ─────────────────────────────────────────────────────────────────

class PDF:
    @staticmethod
    def merge(pdfs: list[str], output_path: Path) -> list[str]:
        """Merge *pdfs* into *output_path*.

        Returns a list of file paths that were skipped because they could
        not be read as valid PDFs.

        Raises:
            FileExistsError: if *output_path* already exists.
            ValueError: if none of the provided files are readable PDFs.
        """
        if output_path.exists():
            raise FileExistsError(str(output_path))

        skipped: list[str] = []
        valid_count = 0
        with pypdf.PdfWriter() as writer:
            for pdf in pdfs:
                if PDF.validate(pdf):
                    writer.append(pdf)
                    valid_count += 1
                else:
                    skipped.append(pdf)

            if valid_count == 0:
                raise ValueError("No valid PDF files to merge.")

            with open(output_path, "wb") as fh:
                writer.write(fh)

        return skipped

    @staticmethod
    def validate(pdf: str) -> bool:
        """Return *True* if *pdf* can be opened and read as a valid PDF."""
        try:
            with open(pdf, "rb") as fh:
                pypdf.PdfReader(fh, strict=False)
            return True
        except (pypdf.errors.PdfReadError, pypdf.errors.EmptyFileError, OSError):
            return False


# ── Localisation ──────────────────────────────────────────────────────────────

LANG_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "select_files":        "Select PDFs",
        "merge_pdfs":          "Merge PDFs",
        "output_name":         "Output PDF Name:",
        "operation_completed": "Operation completed. PDF saved in \"{}\" as \"{}\".",
        "no_pdfs":             "No PDF files have been selected.",
        "move_up":             "Move up",
        "move_down":           "Move down",
        "remove_pdf":          "Remove",
        "no_name":             "Please enter a file name.",
        "no_destination":      "No destination folder set. Select at least one PDF first.",
        "file_exists":         "A file with that name already exists in the destination folder.",
        "no_valid_pdfs":       "None of the selected files could be read as valid PDFs.",
        "some_pdfs_skipped":   "The following files could not be read as valid PDFs and were skipped:\n\n{}",
    },
    "es": {
        "select_files":        "Seleccionar PDFs",
        "merge_pdfs":          "Unir PDFs",
        "output_name":         "Nombre del PDF de salida:",
        "operation_completed": "Operación completada. PDF guardado en \"{}\" como \"{}\".",
        "no_pdfs":             "No se han seleccionado archivos PDF.",
        "move_up":             "Mover hacia arriba",
        "move_down":           "Mover hacia abajo",
        "remove_pdf":          "Eliminar",
        "no_name":             "Por favor, introduzca un nombre de archivo.",
        "no_destination":      "No se ha establecido carpeta de destino. Seleccione al menos un PDF primero.",
        "file_exists":         "Ya existe un archivo con ese nombre en la carpeta de destino.",
        "no_valid_pdfs":       "Ninguno de los archivos seleccionados pudo leerse como PDF válido.",
        "some_pdfs_skipped":   "Los siguientes archivos no pudieron leerse como PDF válidos y fueron omitidos:\n\n{}",
    },
}


# ── GUI ───────────────────────────────────────────────────────────────────────

class PDFMergerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PDF Merger")
        self.root.geometry("600x400")
        self.root.minsize(600, 400)

        self.folder_var = tk.StringVar()
        self.output_name_var = tk.StringVar()
        self.lang_var = tk.StringVar(value="en")

        self._build_ui()

    @property
    def language(self) -> str:
        return self.lang_var.get()

    @property
    def t(self) -> dict[str, str]:
        """Return the translation dictionary for the current language."""
        return LANG_TEXTS[self.language]

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = self.root
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)
        root.grid_columnconfigure(2, weight=1)
        root.grid_rowconfigure(2, weight=1)

        # Language selector
        frame_lang = tk.Frame(root)
        frame_lang.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        tk.Label(frame_lang, text="Language:").pack(side=tk.LEFT, padx=5, pady=10)
        tk.Radiobutton(
            frame_lang, text="English", variable=self.lang_var,
            value="en", command=self._on_language_change,
        ).pack(side=tk.LEFT, padx=5, pady=10)
        tk.Radiobutton(
            frame_lang, text="Español", variable=self.lang_var,
            value="es", command=self._on_language_change,
        ).pack(side=tk.LEFT, padx=5, pady=10)

        # Select files button
        self.select_files_btn = tk.Button(
            root, text=self.t["select_files"], command=self._select_files,
        )
        self.select_files_btn.grid(
            row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew",
        )

        # Listbox + scrollbar
        frame_list = tk.Frame(root)
        frame_list.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        scrollbar = tk.Scrollbar(frame_list, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.file_listbox = tk.Listbox(frame_list, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # List-management buttons
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ew")
        btn_width = 15
        self.move_up_btn = tk.Button(
            btn_frame, text=self.t["move_up"], command=self._move_up, width=btn_width,
        )
        self.move_up_btn.pack(side=tk.LEFT, padx=5, pady=10, expand=True, fill=tk.X)
        self.move_down_btn = tk.Button(
            btn_frame, text=self.t["move_down"], command=self._move_down, width=btn_width,
        )
        self.move_down_btn.pack(side=tk.LEFT, padx=5, pady=10, expand=True, fill=tk.X)
        self.remove_pdf_btn = tk.Button(
            btn_frame, text=self.t["remove_pdf"], command=self._remove_pdf, width=btn_width,
        )
        self.remove_pdf_btn.pack(side=tk.LEFT, padx=5, pady=10, expand=True, fill=tk.X)

        # Output name
        self.output_name_label = tk.Label(root, text=self.t["output_name"])
        self.output_name_label.grid(row=4, column=0, padx=10, pady=10, sticky="e")
        tk.Entry(root, textvariable=self.output_name_var).grid(
            row=4, column=1, columnspan=2, padx=10, pady=10, sticky="ew",
        )

        # Merge button
        self.merge_pdfs_btn = tk.Button(
            root, text=self.t["merge_pdfs"], command=self._merge_pdfs,
        )
        self.merge_pdfs_btn.grid(
            row=5, column=0, columnspan=3, padx=10, pady=10, sticky="ew",
        )

    # ── Event handlers ─────────────────────────────────────────────────────

    def _on_language_change(self) -> None:
        self.select_files_btn.config(text=self.t["select_files"])
        self.merge_pdfs_btn.config(text=self.t["merge_pdfs"])
        self.move_up_btn.config(text=self.t["move_up"])
        self.move_down_btn.config(text=self.t["move_down"])
        self.output_name_label.config(text=self.t["output_name"])
        self.remove_pdf_btn.config(text=self.t["remove_pdf"])

    def _select_files(self) -> None:
        pdf_files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if not pdf_files:
            return  # user cancelled the dialog
        self.folder_var.set(str(Path(pdf_files[0]).parent))
        self.file_listbox.delete(0, tk.END)
        for pdf in pdf_files:
            self.file_listbox.insert(tk.END, pdf)

    def _merge_pdfs(self) -> None:
        destination = self.folder_var.get()
        raw_name = self.output_name_var.get().strip()
        files = list(self.file_listbox.get(0, tk.END))

        if not files:
            messagebox.showerror("Error", self.t["no_pdfs"])
            return

        if not raw_name:
            messagebox.showerror("Error", self.t["no_name"])
            return

        # Strip any path components to prevent directory traversal attacks
        pdfname = Path(raw_name).name
        if not pdfname:
            messagebox.showerror("Error", self.t["no_name"])
            return
        if not pdfname.lower().endswith(".pdf"):
            pdfname += ".pdf"

        if not destination:
            messagebox.showerror("Error", self.t["no_destination"])
            return

        output_path = Path(destination) / pdfname

        try:
            skipped = PDF.merge(files, output_path)
        except FileExistsError:
            messagebox.showerror("Error", self.t["file_exists"])
            return
        except ValueError:
            messagebox.showerror("Error", self.t["no_valid_pdfs"])
            return
        except OSError as exc:
            messagebox.showerror("Error", str(exc))
            return

        if skipped:
            skipped_names = "\n".join(Path(f).name for f in skipped)
            messagebox.showwarning("Warning", self.t["some_pdfs_skipped"].format(skipped_names))

        messagebox.showinfo(
            "Success",
            self.t["operation_completed"].format(destination, pdfname),
        )

    def _move_up(self) -> None:
        try:
            idx = self.file_listbox.curselection()[0]
            if idx > 0:
                item = self.file_listbox.get(idx)
                self.file_listbox.delete(idx)
                self.file_listbox.insert(idx - 1, item)
                self.file_listbox.selection_set(idx - 1)
        except IndexError:
            pass

    def _move_down(self) -> None:
        try:
            idx = self.file_listbox.curselection()[0]
            if idx < self.file_listbox.size() - 1:
                item = self.file_listbox.get(idx)
                self.file_listbox.delete(idx)
                self.file_listbox.insert(idx + 1, item)
                self.file_listbox.selection_set(idx + 1)
        except IndexError:
            pass

    def _remove_pdf(self) -> None:
        try:
            idx = self.file_listbox.curselection()[0]
            self.file_listbox.delete(idx)
        except IndexError:
            pass


if __name__ == "__main__":
    app = tk.Tk()
    PDFMergerApp(app)
    app.mainloop()
