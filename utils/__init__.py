# dashboard/__init__.py
from .utilities import extrair_texto_de_pdf

# Define o que será acessível com "from dashboard import ..."
__all__ = [
    "extrair_texto_de_pdf"
]