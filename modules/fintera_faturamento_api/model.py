from modules.fintera_faturamento_api.fintera_api import Fintera
from modules.fintera_faturamento_api.helper import Helper

import glob
import os
import sys
import numpy as np
import logging

class Model:
    
    # -> None (indica que o método retorna None)
    def __init__(self) -> None:
        self.file_base = None

    def getFintera(self):
        f = Fintera()
        return f

    def getHelper (self):
        h = Helper()
        return h

    def getDataBaseMedicao(self):
        data = self.getFileBaseMedicao()        
        return [{'CNPJ': r['Conta - Organização - CNPJ'][-14:], **r} for r in data]

    def getEntities(self):
        data = self.getDataBaseMedicao()
        config = self.getHelper().getDataByEntity()
        label_rule = self.getHelper().getRuleLabels()

        result = []
        for r in data:
            cnpj = r['CNPJ']

            for con in config[cnpj]:  
                configfDict = {}
                for l in label_rule:
                    configfDict[l] = con[l]
                r.update(configfDict)
           
            if not 'CNPJ Cobrança' in r or not r['CNPJ Cobrança']:
               r['CNPJ Cobrança'] = cnpj
           
            result.append(r)

        return result
    
    def getEntitiesAddValue(self):
        data = self.getEntities()

        #Malwee -> Necessário somar todos os pedidos e cobrar adicional da Matriz
        result = []

        rs_cobrado = self.getHelper().getDataByIndex(data, "CNPJ Cobrança")
        rs_cnpj = self.getHelper().getDataByIndex(data, "CNPJ")

        dict_total = {}
        
        for r in data:            
            if not dict_total.get(r["CNPJ Cobrança"]):
                dict_total[r["CNPJ Cobrança"]] = 0
            dict_total[r["CNPJ Cobrança"]] += r["Qtd de pedidos"]

        #CNPJ Cobrança | Organizacao CNPJ Cobrança | Qtd de pedidos | Pedido Limite | Pedido Add

        for cnpj_cobr in rs_cobrado:
            
            empresa_dict = {}
            for rs in rs_cobrado[cnpj_cobr]:

                if not rs.get('Pedido Limite') or rs['Pedido Limite'] == "Ilimitado":
                    continue
                # else:
                #     print(rs)
                #     sys.exit()

                empresa_dict["CNPJ Cobrança"] = rs["CNPJ Cobrança"]
                empresa_dict['account_id'] = rs['account_id'] 
                empresa_dict['Mês'] = rs['Mês']
                empresa_dict['Qtd de pedidos'] = dict_total[cnpj_cobr]
                empresa_dict['Qtd SKU cadastrados'] = rs['Qtd SKU cadastrados']
                empresa_dict['Pedido Limite'] = rs['Pedido Limite']
                empresa_dict['Pedido Add'] = rs['Pedido Add']

            if 'Pedido Limite' in empresa_dict and isinstance(empresa_dict['Pedido Limite'], (int, float)) and empresa_dict['Qtd de pedidos'] > empresa_dict['Pedido Limite']:
                empresa_dict['Total Add'] = (empresa_dict['Qtd de pedidos']-empresa_dict['Pedido Limite']) * empresa_dict['Pedido Add']
                empresa_dict["Conta - Organização - CNPJ"] = rs_cnpj[cnpj_cobr][0]["Conta - Organização - CNPJ"]
                result.append(empresa_dict)

            # 'Conta - Organização - CNPJ': 'Dream Store - DREAM - ALPHASHOPPING  - 28818969000193', 
            # 'CNPJ': '28818969000193', 


        #Seperar quem é cobrado em grupo e individual
        # for r in data:
        #     if rules.get(r["account_id"]):
        #         rules[r["account_id"]]["total_pedidos"] += r['Qtd de pedidos']
        #         continue
            
        #     if 'Pedido Limite' in r and isinstance(r['Pedido Limite'], (int, float)) and r['Qtd de pedidos'] > r['Pedido Limite']:
        #         r['Total Add'] = (r['Qtd de pedidos']-r['Pedido Limite']) * r['Pedido Add']

        #         result.append(r)
            
        return result

    def prepareCollectionData(self, data, chaves=[]):
        if len(chaves) == 0:
            # Lista de chaves
            chaves = [chave for dicionario in data for chave in dicionario.keys()]

            # Remover duplicatas e manter a ordem
            chaves = list(dict.fromkeys(chaves))            

        lista_valores = []

        for dicionario in data:
            valores = [dicionario[chave] for chave in chaves if chave in dicionario]
            lista_valores.append(valores)

        return chaves, lista_valores
    
    def getEntitiesOnlyRule(self):
        data = self.getDataBaseMedicao()
        config = self.getHelper().getDataByEntity()
        label_rule = self.getHelper().getRuleLabels()

        result = []
        for r in data:
            cnpj = r['CNPJ']

            for con in config[cnpj]:
                configfDict = {}
                for l in label_rule:
                    configfDict[l] = con[l]
                r.update(configfDict)
            
            if not 'Pedido Limite' in r or not r['Pedido Limite']:
                result.append(r)

        return result 

    def getServiceItemFromDataFaturamento(self, data):
        # {
        # "id": 1642,
        # "name": "Nexaas Omni - Assinatura",
        # "description": "Adicionar de pedidos",
        # "unit_value": "100.0",
        # "units": "100.0",
        # "value": "10000.0"
        # }
        dict = {}
        excedente = data["Qtd de pedidos"] - data["Pedido Limite"]
        dict["service_item_id"] = 1642
        dict["name"] = "Nexaas Omni - Assinatura"
        dict["description"] = "Pedidos adicionais"
        dict["unit_value"] = data["Pedido Add"]
        dict["units"] = excedente
        dict["value"] = dict["units"] * dict["unit_value"]
        return dict

    def process(self):
        data_lancamento = self.getEntitiesAddValue()
        fintera = self.getFintera().setEntity("Filial")
        supplier = fintera.getTokens()
        supplier_filial = supplier["Filial"][1]

        logging.basicConfig(filename="alert_log.log", level=logging.INFO, encoding="ISO-8859-1")

        filterDict = self.getHelper().getDueDateParams()
        filterDict.update({"state" : f"to_emit"})

        feed = []
        
        for dt in data_lancamento:
            
            dict = {}
            dict.update(dt)

            service_item_add = self.getServiceItemFromDataFaturamento(dt)
            cnpj = dt['CNPJ Cobrança']
            #Empresa = fintera.getEmpresa(84429737000114)
            Empresa = fintera.getEmpresa(cnpj)

            if Empresa.get("companies"):
                companies = Empresa["companies"]
                customer_id = companies[0]['id']

                # Buscar o contrato usando o id da empresa
                contracts = fintera.getContract(customer_id)
                if contracts.get("contracts"):

                    logging.info(f"Contrato {cnpj} encontrado!")

                    for contract in contracts['contracts']:
                        if supplier_filial != contract['supplier_id']:
                            continue
                        
                        ### Setar o mês atual que o faturamento será feito
                        filterDict = {f"due_date_from" : "01-03-2024", f"due_date_to" : "31-03-2024", f"state" : f"to_emit"}
                        contract_id = contract['id']

                        faturamentos = fintera.getReceivables(contract_id, filterDict)
                        for ft in faturamentos:
                            if ft.get("receivables"):
                                # Buscar qual dos recebíveis é relacionado a licenciamento de software
                                for rc in ft['receivables']:

                                    invoice_id = rc["invoice_id"]
                                    service_add_list = []
                                    if rc.get('invoice'):

                                        #if rc["invoice"].get('services'):
                                        #    for service in rc["invoice"]['services']:
                                        #        pass
                                                #service["id"] = 1642
                                                #service_add_list.append(service)

                                        # Adiciona a compra adicional
                                        service_add_list.append(service_item_add)
                                    else:
                                        logging.info(f"Sem Invoices Associados")

                                    #criar a estrutura para atualização da fatura
                                    updateInvoice = {"invoice": {"services": service_add_list}}
                                    #Chamar a api para atualizar a combrança
                                    response = fintera.updateInvoice(contract_id, invoice_id, updateInvoice)

                            else:
                                logging.info(f"Sem recebíveis associados")
        return True

    def setFileBaseMedicao(self, file):
        self.file_base = file

    def getFileBaseMedicao(self):
        return self.file_base