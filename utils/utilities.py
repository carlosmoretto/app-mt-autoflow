# General utility functions
import pdfplumber

def extrair_texto_de_pdf(caminho_do_arquivo):
    texto = ''
    with pdfplumber.open(caminho_do_arquivo) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text()
    return texto