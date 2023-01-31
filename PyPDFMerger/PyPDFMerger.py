import os
import PyPDF2

import config

class PDF:
    # Method to merge multiple PDFs into one.
    def merge(pdfs, destination, pdfname):
        merger = PyPDF2.PdfMerger()
        result = ''

        if not destination.endswith('\\'): destination = destination + '\\'
        if not pdfname.endswith('.pdf'): pdfname = pdfname + '.pdf'
        result = destination + pdfname

        if os.path.isfile(result): # Check if destination file exists.
            raise Exception('ERROR: Destination file already exists!')
            return

        for pdf in pdfs: # Merge.
            try: merger.append(destination + pdf) # Merge PDFs.
            except PyPDF2.errors.EmptyFileError: continue

        merger.write(destination + pdfname) # Create merged PDF.
        merger.close()


# Method to clear text from the terminal.
def clearScreen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Main
def main():
    pdfs = []
    
    print('\nPlease make sure all your PDF files are in a folder named \'' + config.PDFDir + '\'.')
    print('The folder should be in the same root directory where the app is running.\n')
    print('Current root directory: ' + os.getcwd())
    print('\nPress ENTER to continue..')
    input()
    clearScreen()

    if not os.path.isdir(config.PDFDir): # Check if destination folder exists.
        print('\nNo folder named \'' + config.PDFDir + '\' was detected.\n')
        exit()

    files = os.listdir(config.PDFDir) # Get all files in the specified directory.
    for f in files:
            if f.endswith('.pdf'): pdfs.append(f) # Select only pdfs.

    if not pdfs: # If there are no PDF files.
        print('\nNo valid files were detected.\n')
        exit()

    print('\nThe following PDF files were detected:')
    for pdf in pdfs: print('- ' + pdf)
    key = input('\nInput \'y\' to continue: ')
    clearScreen()

    if key.lower() == 'y':
        try:
            PDF.merge(pdfs, config.PDFDir, config.PDFResultName) # Merge.
            print('\nOperation completed. PDF file saved in \'' + config.PDFDir + '\' as \'' + config.PDFResultName + '\'.')
        except Exception as e: print(str(e))
    else: print('\nOperation canceled.')

    print('')

main()