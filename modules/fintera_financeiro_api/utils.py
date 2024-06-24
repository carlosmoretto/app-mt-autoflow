import requests
from .exceptions import FinteraAPIException

def handle_response(response):
    if response.status_code >= 400:
        raise FinteraAPIException(response.status_code, response.text)
    try:
        return response.json()
    except ValueError:
        return response.text
