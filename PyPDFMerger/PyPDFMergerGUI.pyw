import os
import pypdf
import tkinter as tk
from tkinter import filedialog, messagebox

class PDF:
    @staticmethod
    def merge(pdfs, destination, pdfname):
        merger = pypdf.PdfMerger()
        result = os.path.join(destination, pdfname)
        errormsg = ''

        if os.path.isfile(result):
            if language == 'en': errormsg = 'ERROR: Destination file already exists!'
            elif language == 'es': errormsg = 'ERROR: ¡El archivo de destino ya existe!'
            raise Exception(errormsg)

        for pdf in pdfs:
            if PDF.validate(pdf):
                try:
                    merger.append(pdf)
                except pypdf.errors.EmptyFileError:
                    continue

        merger.write(result)
        merger.close()

    @staticmethod
    def validate(pdf):
        try:
            with open(pdf, 'rb') as file:
                pypdf.PdfReader(file)
            return True
        except (pypdf.errors.PdfReadError, pypdf.errors.EmptyFileError):
            return False

def select_files():
    pdf_files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
    folder_selected = os.path.dirname(pdf_files[0]) if pdf_files else ''
    folder_var.set(folder_selected)
    file_listbox.delete(0, tk.END)
    for pdf in pdf_files:
        file_listbox.insert(tk.END, pdf)

def merge_pdfs():
    try:
        destination = folder_var.get()
        pdfname = output_name_var.get()
        
        files = list(file_listbox.get(0, tk.END))
        if not files:
            raise Exception(lang_texts[language]['no_pdfs'])
        
        if len(pdfname) == 0:
            raise Exception(lang_texts[language]['no_name'])
        
        if not pdfname.endswith('.pdf'):
            pdfname += '.pdf'

        PDF.merge(files, destination, pdfname)
        messagebox.showinfo("Success", lang_texts[language]['operation_completed'].format(destination, pdfname))
    except Exception as e:
        messagebox.showerror("Error", str(e))

def set_language():
    global language
    language = lang_var.get()
    select_files_btn.config(text=lang_texts[language]['select_files'])
    merge_pdfs_btn.config(text=lang_texts[language]['merge_pdfs'])
    move_up_btn.config(text=lang_texts[language]['move_up'])
    move_down_btn.config(text=lang_texts[language]['move_down'])
    output_name_label.config(text=lang_texts[language]['output_name'])
    remove_pdf_btn.config(text=lang_texts[language]['remove_pdf'])

def move_up():
    try:
        selected_idx = file_listbox.curselection()[0]
        if selected_idx > 0:
            item = file_listbox.get(selected_idx)
            file_listbox.delete(selected_idx)
            file_listbox.insert(selected_idx - 1, item)
            file_listbox.selection_set(selected_idx - 1)
    except IndexError:
        pass

def move_down():
    try:
        selected_idx = file_listbox.curselection()[0]
        if selected_idx < file_listbox.size() - 1:
            item = file_listbox.get(selected_idx)
            file_listbox.delete(selected_idx)
            file_listbox.insert(selected_idx + 1, item)
            file_listbox.selection_set(selected_idx + 1)
    except IndexError:
        pass

def remove_pdf():
    try:
        selected_idx = file_listbox.curselection()[0]
        file_listbox.delete(selected_idx)
    except IndexError:
        pass



# Languages
lang_texts = {
    'en': {
        'select_files': 'Select PDFs',
        'merge_pdfs': 'Merge PDFs',
        'output_name': 'Output PDF Name:',
        'operation_completed': 'Operation completed. PDF file saved in "{}" as "{}".',
        'no_pdfs': 'No PDF files were detected in the selected folder.',
        'move_up': 'Move up',
        'move_down': 'Move down',
        'remove_pdf': 'Remove',
        'no_name': 'Please set a file name.'
    },
    'es': {
        'select_files': 'Seleccionar PDFs',
        'merge_pdfs': 'Unir PDFs',
        'output_name': 'Nombre del PDF de salida:',
        'operation_completed': 'Operación completada. Archivo PDF guardado en "{}" como "{}".',
        'no_pdfs': 'No se detectaron archivos PDF en la carpeta seleccionada.',
        'move_up': 'Mover hacia arriba',
        'move_down': 'Mover hacia abajo',
        'remove_pdf': 'Eliminar',
        'no_name': 'Por favor, establezca un nombre de archivo.'
    }
}



# GUI
# Create the main application window
app = tk.Tk()
app.title("PDF Merger")
app.geometry("600x400")
app.minsize(600, 400)

folder_var = tk.StringVar()
output_name_var = tk.StringVar()

lang_var = tk.StringVar(value='en')
language = lang_var.get()

# Configure grid columns and rows
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)
app.grid_columnconfigure(2, weight=1)
app.grid_rowconfigure(2, weight=1) # Configure the row for the Listbox to expand vertically

# Create and place the language frame
frame_lang = tk.Frame(app)
frame_lang.grid(row=0, column=0, padx=10, pady=10, sticky="w")

tk.Label(frame_lang, text="Language:").pack(side=tk.LEFT, padx=5, pady=10)
tk.Radiobutton(frame_lang, text="English", variable=lang_var, value='en', command=set_language).pack(side=tk.LEFT, padx=5, pady=10)
tk.Radiobutton(frame_lang, text="Español", variable=lang_var, value='es', command=set_language).pack(side=tk.LEFT, padx=5, pady=10)

# Create and place the select files button
select_files_btn = tk.Button(app, text=lang_texts[language]['select_files'], command=select_files)
select_files_btn.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

# Create and place the frame containing the listbox and scrollbar
frame = tk.Frame(app)
frame.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

scrollbar = tk.Scrollbar(frame, orient="vertical")
scrollbar.pack(side="right", fill="y")

file_listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
file_listbox.pack(side="left", fill="both", expand=True)
scrollbar.config(command=file_listbox.yview)

# Create a frame to hold the buttons with equal width
button_frame = tk.Frame(app)
button_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

# Create buttons with a fixed width and pack them in the frame
button_width = 15

move_up_btn = tk.Button(button_frame, text=lang_texts[language]['move_up'], command=move_up, width=button_width)
move_up_btn.pack(side=tk.LEFT, padx=5, pady=10, expand=True, fill=tk.X)

move_down_btn = tk.Button(button_frame, text=lang_texts[language]['move_down'], command=move_down, width=button_width)
move_down_btn.pack(side=tk.LEFT, padx=5, pady=10, expand=True, fill=tk.X)

remove_pdf_btn = tk.Button(button_frame, text=lang_texts[language]['remove_pdf'], command=remove_pdf, width=button_width)
remove_pdf_btn.pack(side=tk.LEFT, padx=5, pady=10, expand=True, fill=tk.X)

# Create and place the output name label and entry
output_name_label = tk.Label(app, text=lang_texts[language]['output_name'])
output_name_label.grid(row=4, column=0, padx=10, pady=10, sticky="e")

output_name_entry = tk.Entry(app, textvariable=output_name_var)
output_name_entry.grid(row=4, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

# Create and place the merge PDFs button
merge_pdfs_btn = tk.Button(app, text=lang_texts[language]['merge_pdfs'], command=merge_pdfs)
merge_pdfs_btn.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

# Run the application
app.mainloop()