from urllib.parse import urlencode
from datetime import datetime, timedelta
from collections import defaultdict
import openpyxl
import os
import time
import random
import pandas as pd
import json

class Helper:

	def __init__(self):
		self.sheet = None
		self.Entidade = "Entidade"

	def getSheet(self):
		if not self.sheet:
			self.sheet = self.planilha_para_lista_dicionarios(self.getPath("configuracao.xlsx"))
		return self.sheet

	def getDueDateNextMonthParams(self):

		# Obtém a data atual
		data_atual = datetime.now()

		# Calcula a data do próximo mês
		primeiro_dia_proximo_mes = (data_atual.replace(day=1) + timedelta(days=32)).replace(day=1)
		ultimo_dia_proximo_mes = (primeiro_dia_proximo_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)

		# Formata as datas no formato "DD-MM-YYYY"
		inicio_proximo_mes_formatado = primeiro_dia_proximo_mes.strftime("%d-%m-%Y")
		fim_proximo_mes_formatado = ultimo_dia_proximo_mes.strftime("%d-%m-%Y")

		params = {'issue_date_from': inicio_proximo_mes_formatado, 'issue_date_to': fim_proximo_mes_formatado}
		query_string = urlencode(params)
		return query_string

	def getDueDateParams(self):
		# Obtém a data atual
		data_atual = datetime.now()
		# Define o primeiro dia do mês atual
		primeiro_dia = data_atual.replace(day=1)

		# Obtém o último dia do mês atual
		ultimo_dia = (primeiro_dia + timedelta(days=31)).replace(day=1) - timedelta(days=1)

		# Formata as datas no formato "DD-MM-YYYY"
		primeiro_dia_formatado = primeiro_dia.strftime("%d-%m-%Y")
		ultimo_dia_formatado = ultimo_dia.strftime("%d-%m-%Y")

		return {'issue_date_from': primeiro_dia_formatado, 'issue_date_to': ultimo_dia_formatado}

	def getServicesFromInvoice(self, response):
		#Verifica se existe um chave de serviço
		services = {}
		for r in response:
			if "services" in r:
				for sevice in r['services']:
					if(sevice['name'] == "> Nexaas Omni - Assinatura"):
						if not r['id'] in services:
							services[r['id']] = []
						services[r['id']].append(sevice)
		return services

	def planilha_para_lista_dicionarios(self, arquivo):
		workbook = openpyxl.load_workbook(arquivo)
		sheet = workbook.active

		# Obtém os cabeçalhos da primeira linha
		headers = [cell.value for cell in sheet[1]]

		# Inicializa a lista que conterá os dicionários
		data_list = []

		# Itera sobre as linhas, começando da segunda linha (índice 2)
		for row in sheet.iter_rows(min_row=2, values_only=True):
			# Cria um dicionário combinando cabeçalhos com valores
			data_dict = dict(zip(headers, row))

			if len(data_dict) > 0:
				data_list.append(data_dict)

		workbook.close()
		
		return data_list

	def getPath (self, fileName=''):
		base_path = os.path.dirname(__file__)
		return os.path.join(base_path, fileName)

	# Aqui começo a trabalhar na planilha de configuração cadastradas na planilha de configuração
	def getLimite(self, tipo=""):
		data = self.getSheet()
		index = None

		pedidoLabel = "Pedido Limite"
		pageviewLabel = "Pageview Limite"
  
		if tipo == "pedido":
			index = pedidoLabel
		elif tipo == "pageview":
			index = pageviewLabel
		result = {}
		for r in data:
			if r['CNPJ']:
				if index:
					result[r['CNPJ']] =  {self.Entidade : r[self.Entidade], index : r[index]}
				else:
					result[r['CNPJ']] =  {self.Entidade : r[self.Entidade], pedidoLabel : r[pedidoLabel], pageviewLabel : r[pageviewLabel]}

		return result

	def getAdd(self, tipo=""):
		data = self.getSheet()
		index = None

		pedidoLabel = "Pedido Add"
		pageviewLabel = "Pageview Add"
  
		if tipo == "pedido":
			index = pedidoLabel
		elif tipo == "pageview":
			index = pageviewLabel
		result = {}
		for r in data:
			if r['CNPJ']:    
				if index:
					result[r['CNPJ']] =  {self.Entidade : r[self.Entidade], index : r[index]}
				else:
					result[r['CNPJ']] =  {self.Entidade : r[self.Entidade], pedidoLabel : r[pedidoLabel], pageviewLabel : r[pageviewLabel]}

		return result

	def getDataByEntity(self, CNPJ=None):
		data = self.getSheet()
		result = defaultdict(list)
		for r in data:
			result[r["CNPJ"]].append(r)

		if CNPJ:
			return result.get(CNPJ, [{}])[0]

		return result

	def getDataByIndex(self, data, index, search=None):
		result = {}
		for r in data:
			if not r[index] in result:
				result[r[index]] = []
			result[r[index]].append(r)

		if search:
			if search in result:
				return result[search]
			else:
				return []

		return result

	def getEntitiesNoRules(self):
		data = self.getSheet()
		result = []
		for r in data:
			if (not r['Pedido Limite'] and not  r['Pedido Add']) or r['Pedido Limite'] == "Ilimitado":
				r['Pedido Limite'] = ""
				r['Pedido Add'] = ""

				del r["Regra_1 [Tempo]"]
				del r["Regra_1 [Valor]"]
    
				del r["Regra_2 [Tempo]"]
				del r["Regra_2 [Valor]"]

				del r["Pageview Limite"]
				del r["Pageview Add"]

				result.append(r)
    
		return result
    
	def getRuleLabels (self):
		return [ 'Pedido Limite', 'Pedido Add', 'Regra_1 [Tempo]', 'Regra_1 [Valor]',
          'Regra_2 [Tempo]', 'Regra_2 [Valor]','Pageview Limite','Pageview Add', "CNPJ Cobrança"]

	def retorno_aleatorio(self):
		# Aguarda 5 segundos
		time.sleep(5)
		# Retorna aleatoriamente verdadeiro ou falso
		return random.choice([True, False])