import os
import PyPDF2

import config

# Method to merge multiple PDFs into one.
class PDF:
											 
    def merge(pdfs, destination, pdfname):
        merger = PyPDF2.PdfMerger()
        result = ''
        errormsg = ''

        if not destination.endswith('\\'): destination = destination + '\\'
        if not pdfname.endswith('.pdf'): pdfname = pdfname + '.pdf'
        result = destination + pdfname

        if os.path.isfile(result):  # Check if destination file exists.
            if language == 'en': errormsg = 'ERROR: Destination file already exists!'
            elif language == 'es': errormsg = 'ERROR: ¡El archivo de destino ya existe!'
            raise Exception(errormsg)

        for pdf in pdfs:  # Merge.
            try:
                merger.append(destination + pdf)  # Merge PDFs.
            except PyPDF2.errors.EmptyFileError:
                continue

        merger.write(destination + pdfname)  # Create merged PDF.
        merger.close()


# Method to clear text from the terminal.
def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')


# Main
def main():
    # Allow the user to select a language for the interface.
    print('Select language / Seleccione el idioma:')
    print('1. English')
    print('2. Español')
    lang_choice = input('Enter choice (1 or 2): ')
    if lang_choice == '1': language = 'en'
    elif lang_choice == '2': language = 'es'
    else:
        print('\nInvalid language. Assuming English as default.')
        language = 'en'


    pdfs = []

    if language == 'en':
        print('\nPlease make sure all your PDF files are in a folder named \'' + config.PDFDir + '\'.')
        print('The folder should be in the same root directory where the app is running.\n')
        print('Current root directory: ' + os.getcwd())
        print('\nPress ENTER to continue..')
    elif language == 'es':
        print('\nAsegúrese de que todos sus archivos PDF estén en una carpeta llamada \'' + config.PDFDir + '\'.')
        print('La carpeta debe estar en el mismo directorio raíz donde se ejecuta la aplicación.\n')
        print('Directorio raíz actual: ' + os.getcwd())
        print('\nPresione ENTER para continuar..')

    input()
    clearScreen()

    if not os.path.isdir(config.PDFDir):  # Check if destination folder exists.
        if language == 'en':
            print('\nNo folder named \'' + config.PDFDir + '\' was detected.\n')
        elif language == 'es':
            print('\nNo se detectó ninguna carpeta llamada \'' + config.PDFDir + '\'.\n')
        exit()

    files = os.listdir(config.PDFDir)  # Get all files in the specified directory.
    for f in files:
        if f.endswith('.pdf'):
            pdfs.append(f)  # Select only pdfs.

    if not pdfs:  # If no pdf files were found, then exit.
        clearScreen()
        if language == 'en':
            print('\nNo PDF files were detected.\n')
        elif language == 'es':
            print('\nNo se detectaron archivos PDF.\n')
        return

    if language == 'en':
        print('\nThe following PDF files were detected:')
    elif language == 'es':
        print('\nSe detectaron los siguientes archivos PDF:')

    for pdf in pdfs:
        print('- ' + pdf)

    if language == 'en':
        key = input('\nInput \'y\' to continue: ')
    elif language == 'es':
        key = input('\nIngrese \'y\' para continuar: ')

    clearScreen()

    if key.lower() == 'y':
        try:
            PDF.merge(pdfs, config.PDFDir, config.PDFResultName)  # Merge.
            if language == 'en':
                print('\nOperation completed. PDF file saved in \'' + config.PDFDir + '\' as \'' + config.PDFResultName + '\'.')
            elif language == 'es':
                print('\nOperación completada. Archivo PDF guardado en \'' + config.PDFDir + '\' como \'' + config.PDFResultName + '\'.')
        except Exception as e:
            print(str(e))
    else:
        if language == 'en':
            print('\nOperation canceled.')
        elif language == 'es':
            print('\nOperación cancelada.')

    print('')


# Ensure the global language variable is declared
language = 'en'

if __name__ == "__main__":
    main()