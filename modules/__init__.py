# dashboard/__init__.py

from .chatgpt import get_chatgpt_response

from .main import show_dashboard
from .helpers import create_chart, calculate_statistics

# Define o que será acessível com "from dashboard import ..."
__all__ = [
    "show_dashboard",
    "create_chart",
    "calculate_statistics",
    "get_chatgpt_response"
]