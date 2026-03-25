"""PyPDFMerger – A simple GUI application for merging PDF files."""

from __future__ import annotations

from pathlib import Path

import pypdf
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import font as tkfont


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
        "app_subtitle":        "Combine multiple PDFs into one",
        "select_files":        "Select PDF Files",
        "merge_pdfs":          "Merge PDFs",
        "output_name":         "Output file name",
        "operation_completed": "PDF saved successfully in \"{}\" as \"{}\".",
        "no_pdfs":             "No PDF files have been selected.",
        "move_up":             "\u2191  Move Up",
        "move_down":           "\u2193  Move Down",
        "remove_pdf":          "\u00d7  Remove",
        "no_name":             "Please enter a file name.",
        "no_destination":      "No destination folder set. Select at least one PDF first.",
        "file_exists":         "A file with that name already exists in the destination folder.",
        "no_valid_pdfs":       "None of the selected files could be read as valid PDFs.",
        "some_pdfs_skipped":   "Some files were skipped (invalid PDFs):\n\n{}",
        "files_selected":      "{} file(s) selected",
        "no_files":            "No files selected",
        "destination":         "Destination:",
    },
    "es": {
        "app_subtitle":        "Combina m\u00faltiples PDFs en uno",
        "select_files":        "Seleccionar PDFs",
        "merge_pdfs":          "Unir PDFs",
        "output_name":         "Nombre del archivo de salida",
        "operation_completed": "PDF guardado exitosamente en \"{}\" como \"{}\".",
        "no_pdfs":             "No se han seleccionado archivos PDF.",
        "move_up":             "\u2191  Subir",
        "move_down":           "\u2193  Bajar",
        "remove_pdf":          "\u00d7  Eliminar",
        "no_name":             "Por favor, introduzca un nombre de archivo.",
        "no_destination":      "No se ha establecido carpeta de destino. Seleccione al menos un PDF primero.",
        "file_exists":         "Ya existe un archivo con ese nombre en la carpeta de destino.",
        "no_valid_pdfs":       "Ninguno de los archivos seleccionados pudo leerse como PDF v\u00e1lido.",
        "some_pdfs_skipped":   "Algunos archivos fueron omitidos (PDFs inv\u00e1lidos):\n\n{}",
        "files_selected":      "{} archivo(s) seleccionado(s)",
        "no_files":            "Sin archivos seleccionados",
        "destination":         "Destino:",
    },
}


# ── Theme ──────────────────────────────────────────────────────────────────────

THEME = {
    "bg":              "#f5f5f7",
    "surface":         "#ffffff",
    "primary":         "#0057d8",
    "primary_hover":   "#0046b0",
    "danger":          "#dc2626",
    "danger_hover":    "#b91c1c",
    "neutral":         "#6b7280",
    "neutral_hover":   "#4b5563",
    "text":            "#1d1d1f",
    "text_secondary":  "#6e6e73",
    "border":          "#d2d2d7",
    "list_bg":         "#ffffff",
    "list_select":     "#dbeafe",
    "list_select_fg":  "#1e40af",
    "entry_bg":        "#ffffff",
    "entry_focus":     "#0057d8",
}


# ── GUI ───────────────────────────────────────────────────────────────────────

class PDFMergerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PDF Merger")
        self.root.geometry("700x560")
        self.root.minsize(580, 480)
        self.root.configure(bg=THEME["bg"])

        # Full paths tracked separately from listbox display names
        self._pdf_paths: list[str] = []

        self.folder_var = tk.StringVar()
        self.output_name_var = tk.StringVar()
        self.lang_var = tk.StringVar(value="en")

        self._setup_fonts()
        self._build_ui()

    def _setup_fonts(self) -> None:
        preferred_families = [
            "Segoe UI", "SF Pro Display", "Helvetica Neue",
            "Ubuntu", "DejaVu Sans", "Helvetica",
        ]
        available = set(tkfont.families())
        family = next((f for f in preferred_families if f in available), "TkDefaultFont")

        self.font_heading  = tkfont.Font(family=family, size=15, weight="bold")
        self.font_subtitle = tkfont.Font(family=family, size=9)
        self.font_label    = tkfont.Font(family=family, size=10)
        self.font_btn      = tkfont.Font(family=family, size=10, weight="bold")
        self.font_btn_sm   = tkfont.Font(family=family, size=9)
        self.font_list     = tkfont.Font(family=family, size=9)
        self.font_status   = tkfont.Font(family=family, size=8)

    @property
    def language(self) -> str:
        return self.lang_var.get()

    @property
    def t(self) -> dict[str, str]:
        """Return the translation dictionary for the current language."""
        return LANG_TEXTS[self.language]

    # ── UI helpers ─────────────────────────────────────────────────────────

    def _styled_btn(
        self,
        parent: tk.Widget,
        text: str,
        command,
        bg: str,
        hover_bg: str,
        fg: str = "#ffffff",
        font=None,
    ) -> tk.Button:
        """Return a flat, styled button with an enter/leave hover effect."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            font=font or self.font_btn,
            padx=14,
            pady=8,
        )
        btn.bind("<Enter>", lambda _e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda _e: btn.config(bg=bg))
        return btn

    def _hairline(self, parent: tk.Widget) -> tk.Canvas:
        """Return a 1-px horizontal separator."""
        return tk.Canvas(parent, height=1, bg=THEME["border"], highlightthickness=0)

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = self.root

        # ── Header ──────────────────────────────────────────────────────────
        header = tk.Frame(root, bg=THEME["surface"])
        header.pack(fill="x")

        header_inner = tk.Frame(header, bg=THEME["surface"])
        header_inner.pack(fill="x", padx=24, pady=(16, 14))

        title_row = tk.Frame(header_inner, bg=THEME["surface"])
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text="PDF Merger",
            bg=THEME["surface"],
            fg=THEME["text"],
            font=self.font_heading,
        ).pack(side="left")

        # Language toggle buttons (right side of header)
        lang_frame = tk.Frame(title_row, bg=THEME["surface"])
        lang_frame.pack(side="right", anchor="center")

        tk.Label(
            lang_frame,
            text="Language:",
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=self.font_status,
        ).pack(side="left", padx=(0, 6))

        self._lang_en_btn = tk.Button(
            lang_frame, text="EN",
            command=lambda: self._set_language("en"),
            font=self.font_btn_sm,
            relief="flat", borderwidth=0, cursor="hand2",
            padx=10, pady=4,
        )
        self._lang_en_btn.pack(side="left", padx=(0, 3))

        self._lang_es_btn = tk.Button(
            lang_frame, text="ES",
            command=lambda: self._set_language("es"),
            font=self.font_btn_sm,
            relief="flat", borderwidth=0, cursor="hand2",
            padx=10, pady=4,
        )
        self._lang_es_btn.pack(side="left")

        self.subtitle_label = tk.Label(
            header_inner,
            text=self.t["app_subtitle"],
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=self.font_subtitle,
        )
        self.subtitle_label.pack(anchor="w", pady=(3, 0))

        self._hairline(root).pack(fill="x")

        # ── Body ────────────────────────────────────────────────────────────
        body = tk.Frame(root, bg=THEME["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=16)

        # Select files button
        self.select_files_btn = self._styled_btn(
            body,
            text=self.t["select_files"],
            command=self._select_files,
            bg=THEME["primary"],
            hover_bg=THEME["primary_hover"],
        )
        self.select_files_btn.pack(fill="x", pady=(0, 10))

        # ── File list card ───────────────────────────────────────────────────
        list_card = tk.Frame(
            body,
            bg=THEME["surface"],
            highlightbackground=THEME["border"],
            highlightthickness=1,
        )
        list_card.pack(fill="both", expand=True)

        # Card header: file count + action buttons
        card_header = tk.Frame(list_card, bg=THEME["surface"])
        card_header.pack(fill="x", padx=12, pady=(10, 8))

        self.files_count_label = tk.Label(
            card_header,
            text=self.t["no_files"],
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=self.font_status,
        )
        self.files_count_label.pack(side="left")

        btn_bar = tk.Frame(card_header, bg=THEME["surface"])
        btn_bar.pack(side="right")

        self.move_up_btn = self._styled_btn(
            btn_bar,
            text=self.t["move_up"],
            command=self._move_up,
            bg=THEME["neutral"],
            hover_bg=THEME["neutral_hover"],
            font=self.font_btn_sm,
        )
        self.move_up_btn.pack(side="left", padx=(0, 4))

        self.move_down_btn = self._styled_btn(
            btn_bar,
            text=self.t["move_down"],
            command=self._move_down,
            bg=THEME["neutral"],
            hover_bg=THEME["neutral_hover"],
            font=self.font_btn_sm,
        )
        self.move_down_btn.pack(side="left", padx=(0, 4))

        self.remove_pdf_btn = self._styled_btn(
            btn_bar,
            text=self.t["remove_pdf"],
            command=self._remove_pdf,
            bg=THEME["danger"],
            hover_bg=THEME["danger_hover"],
            font=self.font_btn_sm,
        )
        self.remove_pdf_btn.pack(side="left")

        self._hairline(list_card).pack(fill="x")

        # Listbox with scrollbar
        list_inner = tk.Frame(list_card, bg=THEME["list_bg"])
        list_inner.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_inner, orient="vertical", relief="flat")
        scrollbar.pack(side="right", fill="y")

        self.file_listbox = tk.Listbox(
            list_inner,
            yscrollcommand=scrollbar.set,
            bg=THEME["list_bg"],
            fg=THEME["text"],
            selectbackground=THEME["list_select"],
            selectforeground=THEME["list_select_fg"],
            font=self.font_list,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
        )
        self.file_listbox.pack(side="left", fill="both", expand=True, padx=8, pady=4)
        scrollbar.config(command=self.file_listbox.yview)

        # ── Output name ──────────────────────────────────────────────────────
        output_section = tk.Frame(body, bg=THEME["bg"])
        output_section.pack(fill="x", pady=(12, 0))

        self.output_name_label = tk.Label(
            output_section,
            text=self.t["output_name"],
            bg=THEME["bg"],
            fg=THEME["text"],
            font=self.font_label,
        )
        self.output_name_label.pack(anchor="w", pady=(0, 5))

        self._entry_frame = tk.Frame(
            output_section,
            bg=THEME["entry_bg"],
            highlightbackground=THEME["border"],
            highlightthickness=1,
        )
        self._entry_frame.pack(fill="x")

        self.output_entry = tk.Entry(
            self._entry_frame,
            textvariable=self.output_name_var,
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            relief="flat",
            borderwidth=0,
            font=self.font_label,
            insertbackground=THEME["text"],
        )
        self.output_entry.pack(fill="x", padx=10, pady=8)
        self.output_entry.bind(
            "<FocusIn>",
            lambda _e: self._entry_frame.config(
                highlightbackground=THEME["entry_focus"], highlightthickness=2
            ),
        )
        self.output_entry.bind(
            "<FocusOut>",
            lambda _e: self._entry_frame.config(
                highlightbackground=THEME["border"], highlightthickness=1
            ),
        )

        # ── Merge button ─────────────────────────────────────────────────────
        self.merge_pdfs_btn = self._styled_btn(
            body,
            text=self.t["merge_pdfs"],
            command=self._merge_pdfs,
            bg=THEME["primary"],
            hover_bg=THEME["primary_hover"],
        )
        self.merge_pdfs_btn.pack(fill="x", pady=(12, 0))

        # ── Status bar ───────────────────────────────────────────────────────
        self._hairline(root).pack(fill="x")

        status_bar = tk.Frame(root, bg=THEME["surface"])
        status_bar.pack(fill="x")

        status_inner = tk.Frame(status_bar, bg=THEME["surface"])
        status_inner.pack(fill="x", padx=20, pady=6)

        self._dest_key_label = tk.Label(
            status_inner,
            text=self.t["destination"],
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=self.font_status,
        )
        self._dest_key_label.pack(side="left")

        self.destination_label = tk.Label(
            status_inner,
            text="\u2014",
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=self.font_status,
        )
        self.destination_label.pack(side="left", padx=(4, 0))

        self._update_lang_buttons()

    # ── Internal helpers ───────────────────────────────────────────────────

    def _update_lang_buttons(self) -> None:
        lang = self.language
        for btn, code in ((self._lang_en_btn, "en"), (self._lang_es_btn, "es")):
            if lang == code:
                btn.config(
                    bg=THEME["primary"],
                    fg="#ffffff",
                    activebackground=THEME["primary_hover"],
                    activeforeground="#ffffff",
                )
                btn.unbind("<Enter>")
                btn.unbind("<Leave>")
            else:
                btn.config(
                    bg=THEME["surface"],
                    fg=THEME["text_secondary"],
                    activebackground=THEME["bg"],
                    activeforeground=THEME["text_secondary"],
                )
                btn.bind("<Enter>", lambda _e, b=btn: b.config(bg=THEME["bg"]))
                btn.bind("<Leave>", lambda _e, b=btn: b.config(bg=THEME["surface"]))

    def _update_file_count(self) -> None:
        n = len(self._pdf_paths)
        text = self.t["no_files"] if n == 0 else self.t["files_selected"].format(n)
        self.files_count_label.config(text=text)

    def _refresh_listbox(self) -> None:
        """Repopulate the listbox from *_pdf_paths*, showing only file names."""
        self.file_listbox.delete(0, tk.END)
        for path in self._pdf_paths:
            self.file_listbox.insert(tk.END, f"  {Path(path).name}")

    # ── Event handlers ─────────────────────────────────────────────────────

    def _set_language(self, lang: str) -> None:
        self.lang_var.set(lang)
        self._on_language_change()

    def _on_language_change(self) -> None:
        self.subtitle_label.config(text=self.t["app_subtitle"])
        self.select_files_btn.config(text=self.t["select_files"])
        self.merge_pdfs_btn.config(text=self.t["merge_pdfs"])
        self.move_up_btn.config(text=self.t["move_up"])
        self.move_down_btn.config(text=self.t["move_down"])
        self.output_name_label.config(text=self.t["output_name"])
        self.remove_pdf_btn.config(text=self.t["remove_pdf"])
        self._dest_key_label.config(text=self.t["destination"])
        self._update_lang_buttons()
        self._update_file_count()

    def _select_files(self) -> None:
        pdf_files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if not pdf_files:
            return  # user cancelled the dialog
        self.folder_var.set(str(Path(pdf_files[0]).parent))
        self._pdf_paths = list(pdf_files)
        self._refresh_listbox()
        self._update_file_count()
        self.destination_label.config(text=self.folder_var.get())

    def _merge_pdfs(self) -> None:
        destination = self.folder_var.get()
        raw_name = self.output_name_var.get().strip()
        files = self._pdf_paths

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
        except IndexError:
            return
        if idx > 0:
            self._pdf_paths[idx - 1], self._pdf_paths[idx] = (
                self._pdf_paths[idx],
                self._pdf_paths[idx - 1],
            )
            self._refresh_listbox()
            self.file_listbox.selection_set(idx - 1)

    def _move_down(self) -> None:
        try:
            idx = self.file_listbox.curselection()[0]
        except IndexError:
            return
        if idx < len(self._pdf_paths) - 1:
            self._pdf_paths[idx], self._pdf_paths[idx + 1] = (
                self._pdf_paths[idx + 1],
                self._pdf_paths[idx],
            )
            self._refresh_listbox()
            self.file_listbox.selection_set(idx + 1)

    def _remove_pdf(self) -> None:
        try:
            idx = self.file_listbox.curselection()[0]
        except IndexError:
            return
        del self._pdf_paths[idx]
        self._refresh_listbox()
        self._update_file_count()
        if not self._pdf_paths:
            self.folder_var.set("")
            self.destination_label.config(text="\u2014")


if __name__ == "__main__":
    app = tk.Tk()
    PDFMergerApp(app)
    app.mainloop()
