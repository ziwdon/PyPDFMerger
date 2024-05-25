import os
import PyPDF2
import tkinter as tk
from tkinter import filedialog, messagebox

class PDF:
    @staticmethod
    def merge(pdfs, destination, pdfname):
        merger = PyPDF2.PdfMerger()
        result = os.path.join(destination, pdfname)
        errormsg = ''

        if os.path.isfile(result):
            if language == 'en': errormsg = 'ERROR: Destination file already exists!'
            elif language == 'es': errormsg = 'ERROR: ¡El archivo de destino ya existe!'
            raise Exception(errormsg)

        for pdf in pdfs:
            try:
                merger.append(os.path.join(destination, pdf))
            except PyPDF2.errors.EmptyFileError:
                continue

        merger.write(result)
        merger.close()

def select_folder():
    folder_selected = filedialog.askdirectory()
    folder_var.set(folder_selected)
    if folder_selected:
        files = os.listdir(folder_selected)
        pdfs = [f for f in files if f.endswith('.pdf')]
        file_listbox.delete(0, tk.END)
        for pdf in pdfs:
            file_listbox.insert(tk.END, pdf)

def merge_pdfs():
    try:
        destination = folder_var.get()
        pdfname = output_name_var.get()
        
        # Get PDF files in the list
        files = list(file_listbox.get(0, tk.END))
        if not files:
            raise Exception(lang_texts[language]['no_pdfs'])
        
        # Check if an output file name is set
        if len(pdfname) == 0:
            raise Exception(lang_texts[language]['no_name'])
        
        # Validate file name extension
        if not pdfname.endswith('.pdf'):
            pdfname += '.pdf'

        # Merge PDFs
        PDF.merge(files, destination, pdfname)
        messagebox.showinfo("Success", lang_texts[language]['operation_completed'].format(destination, pdfname))
    except Exception as e:
        messagebox.showerror("Error", str(e))

def set_language():
    global language
    language = lang_var.get()
    select_folder_btn.config(text=lang_texts[language]['select_folder'])
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

app = tk.Tk()
app.title("PDF Merger")

folder_var = tk.StringVar()
output_name_var = tk.StringVar()

lang_texts = {
    'en': {
        'select_folder': 'Select Folder',
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
        'select_folder': 'Seleccionar carpeta',
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

lang_var = tk.StringVar(value='en')
language = lang_var.get()

# Configure grid layout
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)
app.grid_columnconfigure(2, weight=1)

tk.Label(app, text="Language:").grid(row=0, column=0, padx=10, pady=10, sticky="ew")
tk.Radiobutton(app, text="English", variable=lang_var, value='en', command=set_language).grid(row=0, column=1, padx=10, pady=10, sticky="ew")
tk.Radiobutton(app, text="Español", variable=lang_var, value='es', command=set_language).grid(row=0, column=2, padx=10, pady=10, sticky="ew")

select_folder_btn = tk.Button(app, text=lang_texts[language]['select_folder'], command=select_folder)
select_folder_btn.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

file_listbox = tk.Listbox(app, width=50)
file_listbox.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

move_up_btn = tk.Button(app, text=lang_texts[language]['move_up'], command=move_up)
move_up_btn.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
move_down_btn = tk.Button(app, text=lang_texts[language]['move_down'], command=move_down)
move_down_btn.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

remove_pdf_btn = tk.Button(app, text=lang_texts[language]['remove_pdf'], command=remove_pdf)
remove_pdf_btn.grid(row=3, column=2, padx=10, pady=10, sticky="ew")

output_name_label = tk.Label(app, text=lang_texts[language]['output_name'])
output_name_label.grid(row=4, column=0, padx=10, pady=10, sticky="e")

output_name_entry = tk.Entry(app, textvariable=output_name_var)
output_name_entry.grid(row=4, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

merge_pdfs_btn = tk.Button(app, text=lang_texts[language]['merge_pdfs'], command=merge_pdfs)
merge_pdfs_btn.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

app.mainloop()
