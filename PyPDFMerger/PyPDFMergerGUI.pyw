"""PyPDFMerger – A simple GUI application for merging and splitting PDF files."""

from __future__ import annotations

import io
from pathlib import Path
import re
from urllib.parse import unquote, urlparse

import pypdf
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import font as tkfont

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # pragma: no cover - optional dependency at runtime
    DND_FILES = None
    TkinterDnD = None


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
                raise ValueError("no_valid_pdfs")

            with open(output_path, "wb") as fh:
                writer.write(fh)

        return skipped

    @staticmethod
    def split_by_ranges(
        source_pdf: str,
        output_dir: Path,
        output_stem: str,
        ranges_spec: str,
    ) -> list[Path]:
        """Split *source_pdf* into one file per page range expression."""
        reader = PDF._open_reader(source_pdf)
        total_pages = len(reader.pages)
        page_ranges = PDF._parse_page_ranges(ranges_spec, total_pages)

        output_paths: list[Path] = []
        for start, end in page_ranges:
            if start == end:
                filename = f"{output_stem}_page_{start}.pdf"
            else:
                filename = f"{output_stem}_pages_{start}-{end}.pdf"
            output_paths.append(output_dir / filename)

        PDF._ensure_outputs_do_not_exist(output_paths)
        PDF._write_ranges(reader, page_ranges, output_paths)
        return output_paths

    @staticmethod
    def split_every_n(
        source_pdf: str,
        output_dir: Path,
        output_stem: str,
        chunk_size: int,
    ) -> list[Path]:
        """Split *source_pdf* into chunks of *chunk_size* pages."""
        if chunk_size <= 0:
            raise ValueError("invalid_chunk_size")

        reader = PDF._open_reader(source_pdf)
        total_pages = len(reader.pages)
        if total_pages == 0:
            raise ValueError("invalid_source_pdf")

        page_ranges: list[tuple[int, int]] = []
        start = 1
        while start <= total_pages:
            end = min(start + chunk_size - 1, total_pages)
            page_ranges.append((start, end))
            start = end + 1

        output_paths = []
        for index, (range_start, range_end) in enumerate(page_ranges, start=1):
            filename = (
                f"{output_stem}_part_{index:02d}_pages_{range_start}-{range_end}.pdf"
            )
            output_paths.append(output_dir / filename)

        PDF._ensure_outputs_do_not_exist(output_paths)
        PDF._write_ranges(reader, page_ranges, output_paths)
        return output_paths

    @staticmethod
    def split_by_bookmarks(
        source_pdf: str,
        output_dir: Path,
        output_stem: str,
    ) -> list[Path]:
        """Split *source_pdf* by top-level bookmarks / sections."""
        reader = PDF._open_reader(source_pdf)
        total_pages = len(reader.pages)

        sections = PDF._collect_bookmark_sections(reader)
        if not sections:
            raise ValueError("no_bookmarks_found")

        page_ranges: list[tuple[int, int]] = []
        output_paths: list[Path] = []
        for index, (start_page_index, title) in enumerate(sections, start=1):
            if index < len(sections):
                end_page_index = sections[index][0] - 1
            else:
                end_page_index = total_pages - 1

            if end_page_index < start_page_index:
                continue

            # Convert to one-based ranges for naming and write logic.
            start_page = start_page_index + 1
            end_page = end_page_index + 1
            page_ranges.append((start_page, end_page))

            safe_title = PDF._sanitize_component(title) or f"section_{index:02d}"
            filename = f"{output_stem}_{index:02d}_{safe_title}.pdf"
            output_paths.append(output_dir / filename)

        if not output_paths:
            raise ValueError("no_bookmarks_found")

        PDF._ensure_outputs_do_not_exist(output_paths)
        PDF._write_ranges(reader, page_ranges, output_paths)
        return output_paths

    @staticmethod
    def build_output_stem(raw_name: str, fallback: str) -> str:
        """Build a safe output stem from user input and fallback."""
        name = raw_name.strip()
        if name.lower().endswith(".pdf"):
            name = name[:-4]

        sanitized = PDF._sanitize_component(name)
        if sanitized:
            return sanitized
        fallback_sanitized = PDF._sanitize_component(fallback)
        return fallback_sanitized or "output"

    @staticmethod
    def validate(pdf: str) -> bool:
        """Return *True* if *pdf* can be opened and read as a valid PDF."""
        try:
            with open(pdf, "rb") as fh:
                pypdf.PdfReader(fh, strict=False)
            return True
        except (pypdf.errors.PdfReadError, pypdf.errors.EmptyFileError, OSError):
            return False

    @staticmethod
    def _open_reader(pdf: str) -> pypdf.PdfReader:
        if not PDF.validate(pdf):
            raise ValueError("invalid_source_pdf")
        data = Path(pdf).read_bytes()
        reader = pypdf.PdfReader(io.BytesIO(data), strict=False)
        _ = len(reader.pages)
        return reader

    @staticmethod
    def _parse_page_ranges(spec: str, total_pages: int) -> list[tuple[int, int]]:
        if total_pages <= 0:
            raise ValueError("invalid_source_pdf")

        raw_spec = spec.strip()
        if not raw_spec:
            raise ValueError("invalid_page_ranges")

        parsed: list[tuple[int, int]] = []
        for token in raw_spec.split(","):
            item = token.strip()
            if not item:
                raise ValueError("invalid_page_ranges")

            if "-" in item:
                left, right = item.split("-", 1)
                if not left.strip().isdigit() or not right.strip().isdigit():
                    raise ValueError("invalid_page_ranges")
                start = int(left.strip())
                end = int(right.strip())
            else:
                if not item.isdigit():
                    raise ValueError("invalid_page_ranges")
                start = end = int(item)

            if start < 1 or end < 1 or start > end or end > total_pages:
                raise ValueError("invalid_page_ranges")
            parsed.append((start, end))

        if not parsed:
            raise ValueError("invalid_page_ranges")
        return parsed

    @staticmethod
    def _bookmark_page_index(reader: pypdf.PdfReader, item) -> int | None:
        try:
            return reader.get_destination_page_number(item)
        except Exception:
            pass

        try:
            page_obj = getattr(item, "page", None)
            if page_obj is not None:
                return reader.get_page_number(page_obj)
        except Exception:
            return None
        return None

    @staticmethod
    def _bookmark_title(item, fallback: str = "Section") -> str:
        title = getattr(item, "title", None)
        if title:
            return str(title)
        if isinstance(item, dict):
            raw = item.get("/Title") or item.get("title")
            if raw:
                return str(raw)
        return fallback

    @staticmethod
    def _collect_bookmark_sections(reader: pypdf.PdfReader) -> list[tuple[int, str]]:
        try:
            outline = reader.outline
        except Exception:
            return []

        items = outline if isinstance(outline, list) else [outline]
        collected: list[tuple[int, str]] = []
        for item in items:
            # Nested lists are child bookmarks for previous top-level entry.
            if isinstance(item, list):
                continue
            page_index = PDF._bookmark_page_index(reader, item)
            if page_index is None:
                continue
            if page_index < 0 or page_index >= len(reader.pages):
                continue
            collected.append((page_index, PDF._bookmark_title(item)))

        if not collected:
            return []

        # Sort and de-duplicate by starting page, preserving first title.
        ordered = sorted(collected, key=lambda entry: entry[0])
        unique: list[tuple[int, str]] = []
        seen_pages: set[int] = set()
        for page_index, title in ordered:
            if page_index in seen_pages:
                continue
            seen_pages.add(page_index)
            unique.append((page_index, title))

        if unique and unique[0][0] > 0:
            unique.insert(0, (0, "Start"))
        return unique

    @staticmethod
    def _sanitize_component(value: str) -> str:
        cleaned = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", value)
        cleaned = re.sub(r"\s+", "_", cleaned).strip("._ ")
        return cleaned[:80]

    @staticmethod
    def _ensure_outputs_do_not_exist(paths: list[Path]) -> None:
        for path in paths:
            if path.exists():
                raise FileExistsError(str(path))

    @staticmethod
    def _write_ranges(
        reader: pypdf.PdfReader,
        page_ranges: list[tuple[int, int]],
        output_paths: list[Path],
    ) -> None:
        for (start, end), output_path in zip(page_ranges, output_paths):
            writer = pypdf.PdfWriter()
            for page_index in range(start - 1, end):
                writer.add_page(reader.pages[page_index])
            with open(output_path, "wb") as fh:
                writer.write(fh)


# ── Localisation ──────────────────────────────────────────────────────────────

LANG_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "app_title":               "PDF Merger",
        "app_subtitle_merge":      "Combine multiple PDFs into one",
        "app_subtitle_split":      "Split one PDF into multiple files",
        "language_label":          "Language:",
        "operation_label":         "Mode:",
        "mode_merge":              "Merge",
        "mode_split":              "Split",
        "select_files":            "Select PDF Files",
        "select_single_file":      "Select PDF File",
        "merge_pdfs":              "Merge PDFs",
        "split_pdfs":              "Split PDF",
        "output_name":             "Output file name",
        "output_prefix":           "Output prefix (optional)",
        "split_method":            "Split method",
        "split_by_ranges":         "Page range(s)",
        "split_every_n":           "Every N pages",
        "split_by_bookmarks":      "Bookmarks / sections",
        "ranges_label":            "Ranges (e.g. 1-3, 5, 8-10)",
        "every_n_label":           "Pages per file",
        "split_hint_ranges":       "Create one output file per listed range.",
        "split_hint_every_n":      "Split sequentially in fixed-size page chunks.",
        "split_hint_bookmarks":    "Use top-level bookmarks as section boundaries.",
        "operation_completed":     "PDF saved successfully in \"{}\" as \"{}\".",
        "split_completed":         "{} file(s) created successfully in \"{}\".",
        "no_pdfs":                 "No PDF files have been selected.",
        "split_requires_one_pdf":  "Please select exactly one PDF to split.",
        "move_up":                 "\u2191  Move Up",
        "move_down":               "\u2193  Move Down",
        "remove_pdf":              "\u00d7  Remove",
        "clear_all":               "Clear All",
        "choose_output_folder":    "Choose Output Folder",
        "drop_hint":               "Tip: drag PDF files here to add; drag rows to reorder.",
        "no_name":                 "Please enter a file name.",
        "no_destination":          "No destination folder set. Select a PDF first.",
        "file_exists":             "A file with that name already exists in the destination folder.",
        "split_file_exists":       "One output file already exists:\n\n{}",
        "no_valid_pdfs":           "None of the selected files could be read as valid PDFs.",
        "invalid_source_pdf":      "The selected PDF could not be read as a valid PDF.",
        "invalid_page_ranges":     "Invalid page ranges. Use values like: 1-3,5,8-10.",
        "invalid_chunk_size":      "Pages-per-file must be a whole number greater than 0.",
        "no_bookmarks_found":      "No usable bookmarks were found to split this PDF.",
        "some_pdfs_skipped":       "Some files were skipped (invalid PDFs):\n\n{}",
        "duplicate_files_skipped": "These files were already added and were skipped:\n\n{}",
        "non_pdf_files_skipped":   "Only PDF files can be added. Ignored:\n\n{}",
        "split_drop_truncated":    "Split mode only supports one source PDF. The first valid PDF was kept.",
        "files_selected":          "{} file(s) selected",
        "no_files":                "No files selected",
        "destination":             "Destination:",
    },
    "es": {
        "app_title":               "PDF Merger",
        "app_subtitle_merge":      "Combina m\u00faltiples PDFs en uno",
        "app_subtitle_split":      "Divide un PDF en varios archivos",
        "language_label":          "Idioma:",
        "operation_label":         "Modo:",
        "mode_merge":              "Unir",
        "mode_split":              "Dividir",
        "select_files":            "Seleccionar PDFs",
        "select_single_file":      "Seleccionar PDF",
        "merge_pdfs":              "Unir PDFs",
        "split_pdfs":              "Dividir PDF",
        "output_name":             "Nombre del archivo de salida",
        "output_prefix":           "Prefijo de salida (opcional)",
        "split_method":            "M\u00e9todo de divisi\u00f3n",
        "split_by_ranges":         "Rango(s) de p\u00e1ginas",
        "split_every_n":           "Cada N p\u00e1ginas",
        "split_by_bookmarks":      "Marcadores / secciones",
        "ranges_label":            "Rangos (ej. 1-3, 5, 8-10)",
        "every_n_label":           "P\u00e1ginas por archivo",
        "split_hint_ranges":       "Crea un archivo por cada rango indicado.",
        "split_hint_every_n":      "Divide de forma secuencial en bloques fijos.",
        "split_hint_bookmarks":    "Usa marcadores de primer nivel como secciones.",
        "operation_completed":     "PDF guardado exitosamente en \"{}\" como \"{}\".",
        "split_completed":         "{} archivo(s) creado(s) exitosamente en \"{}\".",
        "no_pdfs":                 "No se han seleccionado archivos PDF.",
        "split_requires_one_pdf":  "Seleccione exactamente un PDF para dividir.",
        "move_up":                 "\u2191  Subir",
        "move_down":               "\u2193  Bajar",
        "remove_pdf":              "\u00d7  Eliminar",
        "clear_all":               "Limpiar todo",
        "choose_output_folder":    "Elegir carpeta de salida",
        "drop_hint":               "Consejo: arrastre PDFs aqu\u00ed para agregarlos; arrastre filas para reordenar.",
        "no_name":                 "Por favor, introduzca un nombre de archivo.",
        "no_destination":          "No se ha establecido carpeta de destino. Seleccione un PDF primero.",
        "file_exists":             "Ya existe un archivo con ese nombre en la carpeta de destino.",
        "split_file_exists":       "Uno de los archivos de salida ya existe:\n\n{}",
        "no_valid_pdfs":           "Ninguno de los archivos seleccionados pudo leerse como PDF v\u00e1lido.",
        "invalid_source_pdf":      "El PDF seleccionado no pudo leerse como un PDF v\u00e1lido.",
        "invalid_page_ranges":     "Rangos de p\u00e1gina inv\u00e1lidos. Use algo como: 1-3,5,8-10.",
        "invalid_chunk_size":      "P\u00e1ginas por archivo debe ser un n\u00famero mayor que 0.",
        "no_bookmarks_found":      "No se encontraron marcadores v\u00e1lidos para dividir este PDF.",
        "some_pdfs_skipped":       "Algunos archivos fueron omitidos (PDFs inv\u00e1lidos):\n\n{}",
        "duplicate_files_skipped": "Estos archivos ya estaban agregados y fueron omitidos:\n\n{}",
        "non_pdf_files_skipped":   "Solo se pueden agregar archivos PDF. Ignorados:\n\n{}",
        "split_drop_truncated":    "El modo Dividir solo admite un PDF de origen. Se conserv\u00f3 el primer PDF v\u00e1lido.",
        "files_selected":          "{} archivo(s) seleccionado(s)",
        "no_files":                "Sin archivos seleccionados",
        "destination":             "Destino:",
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
        self.root.geometry("760x680")
        self.root.minsize(620, 560)
        self.root.configure(bg=THEME["bg"])

        # Full paths tracked separately from listbox display names
        self._pdf_paths: list[str] = []
        self._output_folder_explicit = False
        self._drag_index: int | None = None

        self.folder_var = tk.StringVar()
        self.output_name_var = tk.StringVar()
        self.lang_var = tk.StringVar(value="en")
        self.operation_var = tk.StringVar(value="merge")
        self.split_mode_var = tk.StringVar(value="range")
        self.split_ranges_var = tk.StringVar()
        self.split_every_n_var = tk.StringVar(value="1")

        self._setup_fonts()
        self._build_ui()

    def _setup_fonts(self) -> None:
        preferred_families = [
            "Segoe UI", "SF Pro Display", "Helvetica Neue",
            "Ubuntu", "DejaVu Sans", "Helvetica",
        ]
        available = set(tkfont.families())
        family = next((f for f in preferred_families if f in available), "TkDefaultFont")

        self.font_heading = tkfont.Font(family=family, size=15, weight="bold")
        self.font_subtitle = tkfont.Font(family=family, size=9)
        self.font_label = tkfont.Font(family=family, size=10)
        self.font_btn = tkfont.Font(family=family, size=10, weight="bold")
        self.font_btn_sm = tkfont.Font(family=family, size=9)
        self.font_list = tkfont.Font(family=family, size=9)
        self.font_status = tkfont.Font(family=family, size=8)

    @property
    def language(self) -> str:
        return self.lang_var.get()

    @property
    def operation(self) -> str:
        return self.operation_var.get()

    @property
    def split_mode(self) -> str:
        return self.split_mode_var.get()

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

        self.title_label = tk.Label(
            title_row,
            text=self.t["app_title"],
            bg=THEME["surface"],
            fg=THEME["text"],
            font=self.font_heading,
        )
        self.title_label.pack(side="left")

        # Language toggle buttons (right side of header)
        lang_frame = tk.Frame(title_row, bg=THEME["surface"])
        lang_frame.pack(side="right", anchor="center")

        self.language_label = tk.Label(
            lang_frame,
            text=self.t["language_label"],
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=self.font_status,
        )
        self.language_label.pack(side="left", padx=(0, 6))

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
            text=self.t["app_subtitle_merge"],
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=self.font_subtitle,
        )
        self.subtitle_label.pack(anchor="w", pady=(3, 0))

        self._hairline(root).pack(fill="x")

        # ── Body ────────────────────────────────────────────────────────────
        body = tk.Frame(root, bg=THEME["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=16)

        # Mode switch
        mode_card = tk.Frame(
            body,
            bg=THEME["surface"],
            highlightbackground=THEME["border"],
            highlightthickness=1,
        )
        mode_card.pack(fill="x", pady=(0, 10))

        mode_inner = tk.Frame(mode_card, bg=THEME["surface"])
        mode_inner.pack(fill="x", padx=12, pady=10)

        self.operation_label = tk.Label(
            mode_inner,
            text=self.t["operation_label"],
            bg=THEME["surface"],
            fg=THEME["text"],
            font=self.font_label,
        )
        self.operation_label.pack(side="left")

        self.mode_merge_rb = tk.Radiobutton(
            mode_inner,
            text=self.t["mode_merge"],
            variable=self.operation_var,
            value="merge",
            command=self._on_operation_change,
            bg=THEME["surface"],
            fg=THEME["text"],
            selectcolor=THEME["surface"],
            activebackground=THEME["surface"],
            activeforeground=THEME["text"],
            font=self.font_btn_sm,
            padx=8,
            highlightthickness=0,
        )
        self.mode_merge_rb.pack(side="left", padx=(8, 0))

        self.mode_split_rb = tk.Radiobutton(
            mode_inner,
            text=self.t["mode_split"],
            variable=self.operation_var,
            value="split",
            command=self._on_operation_change,
            bg=THEME["surface"],
            fg=THEME["text"],
            selectcolor=THEME["surface"],
            activebackground=THEME["surface"],
            activeforeground=THEME["text"],
            font=self.font_btn_sm,
            padx=8,
            highlightthickness=0,
        )
        self.mode_split_rb.pack(side="left", padx=(8, 0))

        # Select files button
        self.select_files_btn = self._styled_btn(
            body,
            text=self.t["select_files"],
            command=self._select_files,
            bg=THEME["primary"],
            hover_bg=THEME["primary_hover"],
        )
        self.select_files_btn.pack(fill="x", pady=(0, 6))

        self.choose_output_btn = self._styled_btn(
            body,
            text=self.t["choose_output_folder"],
            command=self._choose_output_folder,
            bg=THEME["neutral"],
            hover_bg=THEME["neutral_hover"],
        )
        self.choose_output_btn.pack(fill="x", pady=(0, 10))

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
        self.remove_pdf_btn.pack(side="left", padx=(0, 4))

        self.clear_all_btn = self._styled_btn(
            btn_bar,
            text=self.t["clear_all"],
            command=self._clear_all,
            bg=THEME["neutral"],
            hover_bg=THEME["neutral_hover"],
            font=self.font_btn_sm,
        )
        self.clear_all_btn.pack(side="left")

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
        self.file_listbox.bind("<ButtonPress-1>", self._on_list_press)
        self.file_listbox.bind("<B1-Motion>", self._on_list_drag)
        self.file_listbox.bind("<ButtonRelease-1>", self._on_list_release)

        self.drop_hint_label = tk.Label(
            list_card,
            text=self.t["drop_hint"],
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=self.font_status,
        )
        self.drop_hint_label.pack(anchor="w", padx=12, pady=(0, 8))

        # ── Split options ────────────────────────────────────────────────────
        self.split_options_card = tk.Frame(
            body,
            bg=THEME["surface"],
            highlightbackground=THEME["border"],
            highlightthickness=1,
        )
        self.split_options_card.pack(fill="x", pady=(12, 0))

        split_inner = tk.Frame(self.split_options_card, bg=THEME["surface"])
        split_inner.pack(fill="x", padx=12, pady=10)

        self.split_method_label = tk.Label(
            split_inner,
            text=self.t["split_method"],
            bg=THEME["surface"],
            fg=THEME["text"],
            font=self.font_label,
        )
        self.split_method_label.grid(row=0, column=0, sticky="w")

        methods_row = tk.Frame(split_inner, bg=THEME["surface"])
        methods_row.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.split_range_rb = tk.Radiobutton(
            methods_row,
            text=self.t["split_by_ranges"],
            variable=self.split_mode_var,
            value="range",
            command=self._on_split_mode_change,
            bg=THEME["surface"],
            fg=THEME["text"],
            selectcolor=THEME["surface"],
            activebackground=THEME["surface"],
            activeforeground=THEME["text"],
            font=self.font_btn_sm,
            padx=6,
            highlightthickness=0,
        )
        self.split_range_rb.pack(side="left", padx=(0, 8))

        self.split_every_n_rb = tk.Radiobutton(
            methods_row,
            text=self.t["split_every_n"],
            variable=self.split_mode_var,
            value="every_n",
            command=self._on_split_mode_change,
            bg=THEME["surface"],
            fg=THEME["text"],
            selectcolor=THEME["surface"],
            activebackground=THEME["surface"],
            activeforeground=THEME["text"],
            font=self.font_btn_sm,
            padx=6,
            highlightthickness=0,
        )
        self.split_every_n_rb.pack(side="left", padx=(0, 8))

        self.split_bookmarks_rb = tk.Radiobutton(
            methods_row,
            text=self.t["split_by_bookmarks"],
            variable=self.split_mode_var,
            value="bookmarks",
            command=self._on_split_mode_change,
            bg=THEME["surface"],
            fg=THEME["text"],
            selectcolor=THEME["surface"],
            activebackground=THEME["surface"],
            activeforeground=THEME["text"],
            font=self.font_btn_sm,
            padx=6,
            highlightthickness=0,
        )
        self.split_bookmarks_rb.pack(side="left")

        self.ranges_label = tk.Label(
            split_inner,
            text=self.t["ranges_label"],
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=self.font_status,
        )
        self.ranges_label.grid(row=2, column=0, sticky="w", pady=(10, 3))

        self.ranges_entry = tk.Entry(
            split_inner,
            textvariable=self.split_ranges_var,
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=THEME["border"],
            font=self.font_label,
            insertbackground=THEME["text"],
        )
        self.ranges_entry.grid(row=3, column=0, sticky="ew")

        self.every_n_label = tk.Label(
            split_inner,
            text=self.t["every_n_label"],
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=self.font_status,
        )
        self.every_n_label.grid(row=4, column=0, sticky="w", pady=(10, 3))

        self.every_n_entry = tk.Entry(
            split_inner,
            textvariable=self.split_every_n_var,
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=THEME["border"],
            font=self.font_label,
            insertbackground=THEME["text"],
            width=10,
        )
        self.every_n_entry.grid(row=5, column=0, sticky="w")

        self.split_hint_label = tk.Label(
            split_inner,
            text=self.t["split_hint_ranges"],
            bg=THEME["surface"],
            fg=THEME["text_secondary"],
            font=self.font_status,
        )
        self.split_hint_label.grid(row=6, column=0, sticky="w", pady=(10, 0))

        split_inner.grid_columnconfigure(0, weight=1)

        # ── Output name ──────────────────────────────────────────────────────
        self.output_section = tk.Frame(body, bg=THEME["bg"])
        self.output_section.pack(fill="x", pady=(12, 0))

        self.output_name_label = tk.Label(
            self.output_section,
            text=self.t["output_name"],
            bg=THEME["bg"],
            fg=THEME["text"],
            font=self.font_label,
        )
        self.output_name_label.pack(anchor="w", pady=(0, 5))

        self._entry_frame = tk.Frame(
            self.output_section,
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

        # ── Primary action button ───────────────────────────────────────────
        self.run_action_btn = self._styled_btn(
            body,
            text=self.t["merge_pdfs"],
            command=self._run_action,
            bg=THEME["primary"],
            hover_bg=THEME["primary_hover"],
        )
        self.run_action_btn.pack(fill="x", pady=(12, 0))

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
        self._setup_external_drop()
        self._update_mode_ui()
        self._on_split_mode_change()

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

    def _set_destination(self, folder: str, explicit: bool = False) -> None:
        cleaned = folder.strip()
        self.folder_var.set(cleaned)
        if explicit:
            self._output_folder_explicit = bool(cleaned)
        self.destination_label.config(text=cleaned if cleaned else "\u2014")

    @staticmethod
    def _canonical_path(path: str) -> str:
        return str(Path(path).expanduser().resolve(strict=False))

    def _add_paths(self, candidate_paths: list[str]) -> None:
        if not candidate_paths:
            return

        existing = {self._canonical_path(path) for path in self._pdf_paths}
        duplicates: list[str] = []
        non_pdfs: list[str] = []
        added_any = False

        for raw_path in candidate_paths:
            path = raw_path.strip()
            if not path:
                continue
            path_obj = Path(path)
            if path_obj.suffix.lower() != ".pdf" or not path_obj.exists() or not path_obj.is_file():
                non_pdfs.append(path_obj.name or path)
                continue
            canonical = self._canonical_path(path)
            if canonical in existing:
                duplicates.append(path_obj.name)
                continue
            existing.add(canonical)
            self._pdf_paths.append(str(path_obj))
            added_any = True

        if added_any and not self._output_folder_explicit:
            self._set_destination(str(Path(self._pdf_paths[0]).parent))

        self._refresh_listbox()
        self._update_file_count()

        if duplicates:
            unique = sorted(set(duplicates))
            messagebox.showwarning("Warning", self.t["duplicate_files_skipped"].format("\n".join(unique)))
        if non_pdfs:
            unique = sorted(set(non_pdfs))
            messagebox.showwarning("Warning", self.t["non_pdf_files_skipped"].format("\n".join(unique)))

    def _setup_external_drop(self) -> None:
        if DND_FILES is None:
            return
        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind("<<Drop>>", self._on_external_drop)

    def _parse_drop_paths(self, event_data: str) -> list[str]:
        raw_items = self.root.tk.splitlist(event_data)
        paths: list[str] = []
        for item in raw_items:
            token = item.strip()
            if not token:
                continue
            if token.startswith("file://"):
                parsed = urlparse(token)
                token = unquote(parsed.path)
                if parsed.netloc:
                    token = f"//{parsed.netloc}{token}"
            paths.append(token)
        return paths

    def _update_mode_ui(self) -> None:
        merge_mode = self.operation == "merge"
        self.subtitle_label.config(
            text=self.t["app_subtitle_merge"] if merge_mode else self.t["app_subtitle_split"]
        )
        self.select_files_btn.config(
            text=self.t["select_files"] if merge_mode else self.t["select_single_file"]
        )
        self.output_name_label.config(
            text=self.t["output_name"] if merge_mode else self.t["output_prefix"]
        )
        self.run_action_btn.config(
            text=self.t["merge_pdfs"] if merge_mode else self.t["split_pdfs"]
        )

        if merge_mode:
            self.move_up_btn.config(state="normal")
            self.move_down_btn.config(state="normal")
            if self.split_options_card.winfo_ismapped():
                self.split_options_card.pack_forget()
        else:
            self.move_up_btn.config(state="disabled")
            self.move_down_btn.config(state="disabled")
            if not self.split_options_card.winfo_ismapped():
                self.split_options_card.pack(fill="x", pady=(12, 0), before=self.output_section)

    # ── Event handlers ─────────────────────────────────────────────────────

    def _set_language(self, lang: str) -> None:
        self.lang_var.set(lang)
        self._on_language_change()

    def _on_language_change(self) -> None:
        self.title_label.config(text=self.t["app_title"])
        self.language_label.config(text=self.t["language_label"])
        self.operation_label.config(text=self.t["operation_label"])
        self.mode_merge_rb.config(text=self.t["mode_merge"])
        self.mode_split_rb.config(text=self.t["mode_split"])
        self.move_up_btn.config(text=self.t["move_up"])
        self.move_down_btn.config(text=self.t["move_down"])
        self.remove_pdf_btn.config(text=self.t["remove_pdf"])
        self.clear_all_btn.config(text=self.t["clear_all"])
        self.choose_output_btn.config(text=self.t["choose_output_folder"])
        self.drop_hint_label.config(text=self.t["drop_hint"])
        self._dest_key_label.config(text=self.t["destination"])

        self.split_method_label.config(text=self.t["split_method"])
        self.split_range_rb.config(text=self.t["split_by_ranges"])
        self.split_every_n_rb.config(text=self.t["split_every_n"])
        self.split_bookmarks_rb.config(text=self.t["split_by_bookmarks"])
        self.ranges_label.config(text=self.t["ranges_label"])
        self.every_n_label.config(text=self.t["every_n_label"])

        self._update_lang_buttons()
        self._update_mode_ui()
        self._on_split_mode_change()
        self._update_file_count()

    def _on_operation_change(self) -> None:
        self._update_mode_ui()
        # Keep split workflow strict to one source file.
        if self.operation == "split" and len(self._pdf_paths) > 1:
            self._pdf_paths = self._pdf_paths[:1]
            self._refresh_listbox()
            self._update_file_count()

    def _on_split_mode_change(self) -> None:
        mode = self.split_mode
        if mode == "range":
            self.ranges_entry.config(state="normal")
            self.every_n_entry.config(state="disabled")
            self.split_hint_label.config(text=self.t["split_hint_ranges"])
        elif mode == "every_n":
            self.ranges_entry.config(state="disabled")
            self.every_n_entry.config(state="normal")
            self.split_hint_label.config(text=self.t["split_hint_every_n"])
        else:
            self.ranges_entry.config(state="disabled")
            self.every_n_entry.config(state="disabled")
            self.split_hint_label.config(text=self.t["split_hint_bookmarks"])

    def _select_files(self) -> None:
        if self.operation == "merge":
            selected = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
            if not selected:
                return
            self._add_paths(list(selected))
        else:
            selected = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
            if not selected:
                return
            self._pdf_paths = [selected]
            if not self._output_folder_explicit:
                self._set_destination(str(Path(self._pdf_paths[0]).parent))
            self._refresh_listbox()
            self._update_file_count()

    def _choose_output_folder(self) -> None:
        initial = self.folder_var.get() or str(Path.home())
        folder = filedialog.askdirectory(initialdir=initial)
        if not folder:
            return
        self._set_destination(folder, explicit=True)

    def _on_external_drop(self, event) -> str:
        dropped_paths = self._parse_drop_paths(event.data)
        if not dropped_paths:
            return "break"

        if self.operation == "merge":
            self._add_paths(dropped_paths)
        else:
            pdfs = [path for path in dropped_paths if Path(path).suffix.lower() == ".pdf"]
            if not pdfs:
                messagebox.showwarning("Warning", self.t["non_pdf_files_skipped"].format("\n".join(dropped_paths)))
                return "break"
            self._pdf_paths = [pdfs[0]]
            if len(pdfs) > 1:
                messagebox.showwarning("Warning", self.t["split_drop_truncated"])
            if not self._output_folder_explicit:
                self._set_destination(str(Path(self._pdf_paths[0]).parent))
            self._refresh_listbox()
            self._update_file_count()
        return "break"

    def _run_action(self) -> None:
        if self.operation == "merge":
            self._merge_pdfs()
        else:
            self._split_pdf()

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
        except ValueError as exc:
            key = str(exc)
            messagebox.showerror("Error", self.t.get(key, self.t["no_valid_pdfs"]))
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

    def _split_pdf(self) -> None:
        files = self._pdf_paths
        destination = self.folder_var.get()

        if len(files) != 1:
            messagebox.showerror("Error", self.t["split_requires_one_pdf"])
            return
        if not destination:
            messagebox.showerror("Error", self.t["no_destination"])
            return

        source_pdf = files[0]
        source_stem = Path(source_pdf).stem
        output_stem = PDF.build_output_stem(self.output_name_var.get(), source_stem)
        output_dir = Path(destination)

        try:
            if self.split_mode == "range":
                created = PDF.split_by_ranges(
                    source_pdf,
                    output_dir,
                    output_stem,
                    self.split_ranges_var.get(),
                )
            elif self.split_mode == "every_n":
                try:
                    chunk_size = int(self.split_every_n_var.get().strip())
                except ValueError:
                    raise ValueError("invalid_chunk_size") from None
                created = PDF.split_every_n(source_pdf, output_dir, output_stem, chunk_size)
            else:
                created = PDF.split_by_bookmarks(source_pdf, output_dir, output_stem)
        except FileExistsError as exc:
            messagebox.showerror("Error", self.t["split_file_exists"].format(Path(str(exc)).name))
            return
        except ValueError as exc:
            key = str(exc)
            messagebox.showerror("Error", self.t.get(key, key))
            return
        except OSError as exc:
            messagebox.showerror("Error", str(exc))
            return

        messagebox.showinfo(
            "Success",
            self.t["split_completed"].format(len(created), destination),
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
        if not self._pdf_paths and not self._output_folder_explicit:
            self._set_destination("")

    def _clear_all(self) -> None:
        if not self._pdf_paths:
            return
        self._pdf_paths.clear()
        self._refresh_listbox()
        self._update_file_count()
        if not self._output_folder_explicit:
            self._set_destination("")

    def _on_list_press(self, event: tk.Event) -> None:
        if self.operation != "merge" or not self._pdf_paths:
            self._drag_index = None
            return
        idx = self.file_listbox.nearest(event.y)
        if 0 <= idx < len(self._pdf_paths):
            self._drag_index = idx
            self.file_listbox.selection_clear(0, tk.END)
            self.file_listbox.selection_set(idx)

    def _on_list_drag(self, event: tk.Event) -> None:
        if self.operation != "merge":
            return
        if self._drag_index is None:
            return
        target = self.file_listbox.nearest(event.y)
        if not 0 <= target < len(self._pdf_paths):
            return
        if target == self._drag_index:
            return

        item = self._pdf_paths.pop(self._drag_index)
        self._pdf_paths.insert(target, item)
        self._drag_index = target
        self._refresh_listbox()
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(target)
        self.file_listbox.activate(target)

    def _on_list_release(self, _event: tk.Event) -> None:
        self._drag_index = None


if __name__ == "__main__":
    app = TkinterDnD.Tk() if TkinterDnD is not None else tk.Tk()
    PDFMergerApp(app)
    app.mainloop()
