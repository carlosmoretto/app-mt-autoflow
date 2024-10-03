from urllib.parse import urlencode
import requests
from collections import OrderedDict
import json
import os
import logging
import sys
import streamlit as st
import time

class Fintera:

    def __init__(self):
        self.base_url = "https://faturamento.fintera.com.br/"
        self.headers = {}
        self.organization_id = None

    def validadeEntity (self):
        if self.organization_id is None or len(self.headers) == 0:
            raise ValueError("Entity wasn't difined")

    # def getInvoice(self, contract_id, params):
    #     url = f"{self.base_url}contracts/{contract_id}/invoices/search?{params}"

    #     response = requests.get(url, headers=self.headers)
    #     if response.status_code == 200:
    #         return response.json()
    #     else:
    #         return None

    def getTokens(self):
        # FGP Desenvolvimento de Software LTDA (14.209.764/0001-04)
        tokens = {
            "FGP" : (st.secrets.api.FINTERA_FATU_FGP, 38602) ,
            "Filial" : (st.secrets.api.FINTERA_FATU_FILIAL, 24448),
            "Matriz" : (st.secrets.api.FINTERA_FATU_MATRIZ, 775),
        }
        return tokens

    def setEntity(self, entity):
        tokens = self.getTokens()
        if entity in tokens:
            hash = tokens[entity][0]
            self.organization_id = tokens[entity][1]
            self.headers = { 'Authorization': f'Token token={hash}', 'Content-Type': f'application/json' }
        else:
            raise ValueError("Entity doesn't exist")
        
        return self

    def getContracts(self):
        self.validadeEntity()
        url = f"{self.base_url}api/v1/organizations/{self.organization_id}/contracts"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            return None
        
    def getContract(self, customer_id):
        self.validadeEntity()
        url = f"{self.base_url}api/v1/contracts/search?customer_id={customer_id}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            return None        
    
    def getEmpresa(self, cnpj):
        self.validadeEntity()
        url = f"{self.base_url}api/v1/companies/search?cnpj={cnpj}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            return None
    
    def getReceivables(self, contract_id=None, args={}):
        #to_emit: recebimentos a faturar
        #to_receive: recebimentos a receber
        #received: recebimentos recebidos
        #cancelled: recebimentos cancelados
        #due_date_from=01-01-2022&due_date_to=31-12-2022

        if (len(args) == 0):
            raise ValueError("argments required")
        
        if contract_id is None:
            #Validação inicial
            contracts = self.getContracts()
        else:
            contracts = {"contracts": [{"id": contract_id}]}
    
        contract_list = []
        if(contracts):
            for r in contracts["contracts"]:
                contract_id = r['id']
                url = self.full_url_base(f"api/v1/contracts/{contract_id}/receivables/search?{urlencode(args)}")
                response = requests.get(url, headers=self.headers)

                if response.status_code == 200:
                    contract_dic = response.json()
                    if "receivables" in contract_dic:
                        if len(contract_dic["receivables"]) > 0:
                            r.update(contract_dic)
                            contract_list.append(r)

        return contract_list

    def getInvoice(self, organization_id, params=dict):
        invoices = []  # Lista para armazenar todos os registros acumulados
        page = 1       # Inicializa a contagem de páginas
        seen_invoice_ids = set()  # Conjunto para rastrear IDs já vistos
        
        # Adiciona parâmetros de paginação
        if params is None:
            params = {}

        params['per_page'] = 50  # Define quantos registros por página

        while True:
            params["page"] = page  # Atualiza o número da página na requisição
            query_string = urlencode(params)
            url = self.full_url_base(f"api/v1/organizations/{organization_id}/invoices/search?{query_string}")
            print(url)

            response = requests.get(url, headers=self.headers)

            if response.status_code != 200:
                break

            data = response.json()
            if data.get('invoices') and len(data['invoices']) > 0:
                print( len(data['invoices']) )
                for invoice in data['invoices']:
                    # Verificar se o ID da invoice já foi visto
                    invoice_id = invoice.get('id')
                    if invoice_id not in seen_invoice_ids:
                        invoices.append(invoice)  # Adiciona apenas invoices únicas
                        seen_invoice_ids.add(invoice_id)  # Adiciona o ID ao conjunto
                    else:
                        print('ids repetidos')
                        print(invoice_id)
                page += 1
            else:
                break

            if page == 8:  # Limitação de 8 páginas (ajuste se necessário)
                break

        time.sleep(5)

        return invoices

    def full_url_base (self, url_complement):
        return f"{self.base_url}{url_complement}"
        
    def getServiceItems(self, service_name):
        self.validadeEntity()
        url = f"{self.base_url}api/v1/service_items"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            return None

    def updateInvoice(self, contract_id, invoice_id, data):

        self.validadeEntity()
        url = f"{self.base_url}api/v1/contracts/{contract_id}/invoices/{invoice_id}"
        response = requests.patch(url, headers=self.headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            return None

# f = Fintera()
# rs = f.setEntity("Filial").getAttachments()
# print(rs)

#params = {f"due_date_from" : "01-01-2024", f"due_date_to" : "07-02-2024", f"state" : f"to_receive"}
#recebiveis = f.getReceivables(params)
#print(recebiveis)

#contracts = f.getContracts()

#Função usada para salvar um dicionário em um arquivo

#with open("dict.json", "w") as f:
#    json.dump(contracts, f, indent=4)

# diretorio_arquivo = os.path.dirname(__file__)

#print(diretorio_arquivo)
#exit

# with open(f"{diretorio_arquivo}\dict.json", "r") as f:
#     dicionario = json.load(f)

# logging.basicConfig(filename=f"{diretorio_arquivo}\meu_log.log", level=logging.INFO, encoding="ISO-8859-1")

# for r in dicionario["contracts"]:
#     logging.info(f"Contrato: {r['name']}")
#     logging.info(f"Comments: {r['comments']}")