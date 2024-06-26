import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urlencode
from .exceptions import FinteraAPIException
from .utils import handle_response

class FinteraAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            "ACCOUNT_ID" : "25"
        }

    def list_payable_accounts(self, entity_id, type, params=None):
        accounts = []  # Lista para armazenar todos os registros acumulados
        page = 1       # Inicializa a contagem de páginas
        
        # Adiciona parâmetros de paginação
        if params is None:
            params = {}
        params['per_page'] = 50  # Define quantos registros por página

        while True:
            params['page'] = page  # Atualiza o número da página na requisição
            query_string = urlencode(params)
            url = f'{self.base_url}/entities/{entity_id}/{type}?{query_string}'
            
            response = requests.get(url, headers=self.headers, auth=HTTPBasicAuth(self.token, ''))
            data = handle_response(response)  # Supondo que handle_response retorne os dados já deserializados
            
            # Verifica se a resposta está vazia
            if not data:
                break  # Se não houver dados, sai do loop
            
            accounts.extend(data)  # Adiciona os dados recuperados à lista total
            page += 1  # Incrementa a página para a próxima iteração

        return accounts    
    
    def list_entities(self):
        url = f'{self.base_url}/entities'
        response = requests.get(url, headers=self.headers, auth=HTTPBasicAuth(self.token, ''))
        return handle_response(response)

    def list_attachments(self, entity_id):
        url = f'{self.base_url}/entities/{entity_id}/attachments?per_page=30'
        response = requests.get(url, headers=self.headers, auth=HTTPBasicAuth(self.token, ''))
        return handle_response(response)

    def get_deposit_accounts(self, entity_id, deposit_account_id):
        url = f'{self.base_url}/entities/{entity_id}/deposit_accounts/{deposit_account_id}'
        response = requests.get(url, headers=self.headers, auth=HTTPBasicAuth(self.token, ''))
        return handle_response(response)

    def get_payable_account(self, account_id):
        url = f'{self.base_url}/payable_accounts/{account_id}'
        response = requests.get(url, headers=self.headers)
        return handle_response(response)

    def create_payable_account(self, account_data):
        url = f'{self.base_url}/payable_accounts'
        response = requests.post(url, headers=self.headers, json=account_data)
        return handle_response(response)

    def update_payable_account(self, account_id, account_data):
        url = f'{self.base_url}/payable_accounts/{account_id}'
        response = requests.put(url, headers=self.headers, json=account_data)
        return handle_response(response)

    def delete_payable_account(self, account_id):
        url = f'{self.base_url}/payable_accounts/{account_id}'
        response = requests.delete(url, headers=self.headers)
        return handle_response(response)
