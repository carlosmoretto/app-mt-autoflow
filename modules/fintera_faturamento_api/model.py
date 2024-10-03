from modules.fintera_faturamento_api.fintera_api import Fintera
from modules.fintera_faturamento_api.helper import Helper
from modules.fintera_faturamento_api.faturamento_lock import LockManager

import glob
import os
import sys
import numpy as np
import logging
import calendar
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

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

    def getFilterDict(self, data, meses=0):
        # Obtendo o último dia do mês da data original
        ultimo_dia = calendar.monthrange(data.year, data.month)[1]

        # Criando as datas de início e fim como objetos date
        start_date = data.replace(day=1).date()
        end_date = data.replace(day=ultimo_dia).date()

        # Adicionando o número de meses à data final (end_date)
        end_date_adjusted = end_date + relativedelta(months=meses)

        # Formatando as datas no formato "d-m-YYYY"
        start_date_str = f"{start_date.day}-{start_date.month}-{start_date.year}"
        end_date_str = f"{end_date_adjusted.day}-{end_date_adjusted.month}-{end_date_adjusted.year}"

        # Retornando o dicionário com as datas formatadas
        return {
            "due_date_from": start_date_str,
            "due_date_to": end_date_str,
            "state": "to_emit"
        }

    def process(self):
        data_lancamento = self.getEntitiesAddValue()

        fintera = self.getFintera().setEntity("Filial")
        supplier = fintera.getTokens()
        supplier_filial = supplier["Filial"][1]

        logging.basicConfig(filename="alert_log.log", level=logging.INFO, encoding="ISO-8859-1")
       
        for dt in data_lancamento:

            #filtro para buscar o recebível
            filterDict = self.getFilterDict(dt['Mês'])

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
                                    #response = fintera.updateInvoice(contract_id, invoice_id, updateInvoice)

                            else:
                                logging.info(f"Sem recebíveis associados")
        return True

    def getRules(self):
        rules = pd.DataFrame(self.getHelper().getSheet())
        rules['CNPJ Cobrança'] = rules['CNPJ Cobrança'].fillna(rules['CNPJ'])
        df = rules.dropna(subset=['CNPJ'])
        return df

    def previewDescriptions(self):
        fintera = self.getFintera().setEntity("Filial")
        supplier = fintera.getTokens()
        supplier_filial = supplier["Filial"][1]

        # Medições - arquivo carregado no front
        all_medicao_file = pd.DataFrame(self.getDataBaseMedicao())

        # Extrair a competência única e garantir que é uma string (ex: "2024-10")
        competencia_array = all_medicao_file['Mês'].unique()
        competencia = competencia_array[0].strftime("%Y-%m")  # Pegando o primeiro valor e convertendo para string
        
        competencia_filter_ini = competencia_array[0] + relativedelta(months=1)
        ultimo_dia = calendar.monthrange(competencia_filter_ini.year, competencia_filter_ini.month)[1]
        competencia_filter_fim = competencia_filter_ini.replace(day=ultimo_dia) + relativedelta(months=1)

        # Conjunto das regras para aplicação de valores adicionais e CNPJ de cobrança
        # df_rules = pd.DataFrame(self.getEntities())
        df_rules = self.getRules()

        preview = []

        # Agrupar os CNPJs que vão receber a descrição no sistema.
        for cnpj in df_rules['CNPJ Cobrança'].unique():

            # Flag de controle de atualização
            atualizar = False
            alert = ""

            # Verificar se o CNPJ já foi processado para essa competência

            # totas as organizações na planilha de regras: configuracao.xlsx
            cnpj_organizacao_rules = df_rules[df_rules['CNPJ Cobrança'] == cnpj]

            # Busca na planilha de medição: calcular quantos pedidos de todas as organizações da planilha de regras: configuracao.xlsx
            numero_pedidos = all_medicao_file.loc[all_medicao_file['cnpj'].isin(cnpj_organizacao_rules['CNPJ']), 'Qtd de pedidos'].sum()
            numero_pedidos = int(numero_pedidos)

            # numero de organizações calculadas
            numero_organizacoes = all_medicao_file.loc[all_medicao_file['cnpj'].isin(cnpj_organizacao_rules['CNPJ'])]['cnpj'].count()

            # numero_organizacoes = cnpj_organizacao_rules['cnpj'].count()
            # msg = f"CNPJ cobrança: {cnpj}\nNúmero de pedidos: {numero_pedidos}\nQuantidade de organizações: {numero_organizacoes}"
            msg = f"Quantidade de pedidos {competencia}: {numero_pedidos}"

            # Buscar pelo CNPJ da empresa que tem a regra na planilha configuração
            Empresa = fintera.getEmpresa(cnpj)

            # Verificar se a empresa foi encontrada
            if not Empresa.get("companies"):
                alert = f'Fintera não encontrou a empresa da regra. CNPJ: {cnpj}'
                continue

            empresa_id = Empresa['companies'][0]['id']
            empresa_name = Empresa['companies'][0]['name']

            contracts = fintera.getContract(empresa_id)
            if not contracts.get("contracts"):
                alert = f'Fintera não encontrou contratos para empresa com CNPJ: {cnpj}'
                continue

            contract_id = None
            descripion = None
            descripion_ant = None
            invoice_id = None

            # import pdb;pdb.set_trace()
            #filtra apenas por contratos da filial e ativos
            filter_contract = [r for r in contracts['contracts'] if r['supplier_id'] == supplier_filial and r['status'] == 'established']

            if len(filter_contract) == 0:
                alert = f'Não foi encontrado contratos ativos ou da MYFC Filial para este: {cnpj}'

            # Apenas contratos da filial
            for contract in filter_contract:

                # Contract ID para atualização
                contract_id = contract['id']

                faturamentos = fintera.getReceivables(contract_id, self.getFilterDict(competencia_filter_ini, 3))
                if len(faturamentos) > 0 and faturamentos[0].get('receivables'):

                    invoice_list = [r['invoice'] for r in faturamentos[0]['receivables'] if len(r['invoice']) > 0]

                    df_invoice = pd.DataFrame(invoice_list)

                    # estimated_issue_date - Data de faturamento
                    df_invoice['estimated_issue_date'] = pd.to_datetime(df_invoice['estimated_issue_date'], dayfirst=True)

                    # filtrar por data de faturamento
                    df_invoice = df_invoice[(df_invoice['estimated_issue_date'] >= competencia_filter_ini) & (df_invoice['estimated_issue_date'] <= competencia_filter_fim)]

                    if df_invoice['id'].count() == 0:
                        alert = f'Sem cobranças para faturar para o CNPJ: {cnpj}'
                        continue

                    if len(df_invoice) > 1:
                        # regra de excessão para malwee
                        if cnpj == '84429737000114':
                            index_max = df_invoice['gross_value'].idxmax()
                            df_invoice = df_invoice.loc[[index_max]]
                        else:
                            df_invoice = df_invoice[df_invoice['finance_category_id'] == 4471638].head(1)

                        if len(df_invoice) == 0:
                            alert = f'Não foi possível identificar em qual recebível a descrição vai ser atualizada CNPJ: {cnpj}'
                            continue

                    # obtem o invoice_id para atualização
                    invoice_id = int(df_invoice['id'].values[0])

                    #criar a descrição para atualização
                    is_empty = df_invoice['description'].isna().iloc[0] or df_invoice['description'].iloc[0].strip() == ''
                    if is_empty:
                        descripion = msg
                    else:
                        descripion = df_invoice['description'].iloc[0] + '\n\r\n\r' + msg
                        logging.debug(f"Company: {empresa_id} - Descrição: {df_invoice['description']}")

                    descripion_ant = df_invoice['description'].iloc[0]

                    atualizar = True
                else:
                    alert = f"Não foi encontrado recebíveis para o CNPJ: {cnpj}"

            preview.append({'empresa_name':empresa_name, 
                            'empresa_id':empresa_id,
                                'cnpj': cnpj, 
                                'contract_id': contract_id,
                                'invoice_id': invoice_id,
                                'qtd_organization': numero_organizacoes,
                                'competencia':competencia,
                                'data_atualizacao': datetime.now(),
                                'pedidos':numero_pedidos, 
                                'atualizado':atualizar,
                                'link': f"https://faturamento.fintera.com.br/contracts/{contract_id}/invoices/{invoice_id}/edit",
                                'desc_ant': descripion_ant,
                                'desc_new' : descripion,
                                'alerta': alert})

        return preview

    def processDescription(self):
        logging.basicConfig(filename="atualizacao.log", 
                            level=logging.INFO, 
                            encoding='utf-8',
                            format="%(asctime)s - %(levelname)s - %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")

        fintera = self.getFintera().setEntity("Filial")
        supplier = fintera.getTokens()
        supplier_filial = supplier["Filial"][1]

        # Medições - arquivo carregado no front
        all_medicao_file = pd.DataFrame(self.getDataBaseMedicao())

        # Extrair a competência única e garantir que é uma string (ex: "2024-10")
        competencia_array = all_medicao_file['Mês'].unique()
        competencia = competencia_array[0].strftime("%Y-%m")  # Pegando o primeiro valor e convertendo para string
        
        competencia_filter_ini = competencia_array[0] + relativedelta(months=1)
        ultimo_dia = calendar.monthrange(competencia_filter_ini.year, competencia_filter_ini.month)[1]
        competencia_filter_fim = competencia_filter_ini.replace(day=ultimo_dia) + relativedelta(months=1)

        lock_manager = LockManager('locks.json')

        # Conjunto das regras para aplicação de valores adicionais e CNPJ de cobrança
        # df_rules = pd.DataFrame(self.getEntities())
        df_rules = self.getRules()
        if len(lock_manager.get_cnpj(competencia)) > 0:
            df_rules = df_rules[~df_rules['CNPJ Cobrança'].isin(lock_manager.get_cnpj(competencia))]

        preview = []

        # Agrupar os CNPJs que vão receber a descrição no sistema.
        for cnpj in df_rules['CNPJ Cobrança'].unique():

            # Flag de controle de atualização
            atualizar = False
            alert = ""

            # Verificar se o CNPJ já foi processado para essa competência
            if not lock_manager.check_cnpj_date_lock(competencia, cnpj):

                # totas as organizações na planilha de regras: configuracao.xlsx
                cnpj_organizacao_rules = df_rules[df_rules['CNPJ Cobrança'] == cnpj]

                # Busca na planilha de medição: calcular quantos pedidos de todas as organizações da planilha de regras: configuracao.xlsx
                numero_pedidos = all_medicao_file.loc[all_medicao_file['cnpj'].isin(cnpj_organizacao_rules['CNPJ']), 'Qtd de pedidos'].sum()
                numero_pedidos = int(numero_pedidos)

                # numero de organizações calculadas
                numero_organizacoes = all_medicao_file.loc[all_medicao_file['cnpj'].isin(cnpj_organizacao_rules['CNPJ'])]['cnpj'].count()

                # numero_organizacoes = cnpj_organizacao_rules['cnpj'].count()
                # msg = f"CNPJ cobrança: {cnpj}\nNúmero de pedidos: {numero_pedidos}\nQuantidade de organizações: {numero_organizacoes}"
                msg = f"Quantidade de pedidos {competencia}: {numero_pedidos}"

                # Buscar pelo CNPJ da empresa que tem a regra na planilha configuração
                Empresa = fintera.getEmpresa(cnpj)

                # Verificar se a empresa foi encontrada
                if not Empresa.get("companies"):
                    alert = f'Fintera não encontrou a empresa da regra. CNPJ: {cnpj}'
                    logging.warning(alert)
                    continue

                empresa_id = Empresa['companies'][0]['id']
                empresa_name = Empresa['companies'][0]['name']

                contracts = fintera.getContract(empresa_id)
                if not contracts.get("contracts"):
                    alert = f'Fintera não encontrou contratos para empresa com CNPJ: {cnpj}'
                    logging.warning(alert)
                    continue

                contract_id = None
                descripion = None
                descripion_ant = None
                invoice_id = None

                #filtra apenas por contratos da filial e ativos
                filter_contract = [r for r in contracts['contracts'] if r['supplier_id'] == supplier_filial and r['status'] == 'established']

                if len(filter_contract) == 0:
                    alert = f'Não foi encontrado contratos ativos ou da MYFC Filial para este: {cnpj}'
                    logging.warning(alert)

                # Apenas contratos da filial
                for contract in filter_contract:

                    # Contract ID para atualização
                    contract_id = contract['id']

                    faturamentos = fintera.getReceivables(contract_id, self.getFilterDict(competencia_filter_ini, 3))
                    if len(faturamentos) > 0 and faturamentos[0].get('receivables'):

                        invoice_list = [r['invoice'] for r in faturamentos[0]['receivables'] if len(r['invoice']) > 0]

                        df_invoice = pd.DataFrame(invoice_list)

                        # estimated_issue_date - Data de faturamento
                        df_invoice['estimated_issue_date'] = pd.to_datetime(df_invoice['estimated_issue_date'], dayfirst=True)

                        # filtrar por data de faturamento
                        df_invoice = df_invoice[(df_invoice['estimated_issue_date'] >= competencia_filter_ini) & (df_invoice['estimated_issue_date'] <= competencia_filter_fim)]

                        if df_invoice['id'].count() == 0:
                            logging.warning(f'Sem cobranças para faturar para o CNPJ: {cnpj}')
                            continue

                        if len(df_invoice) > 1:
                            logging.warning(f'Mais de uma invoice para ser faturamento no CNPJ: {cnpj}')
                            # regra de excessão para malwee
                            if cnpj == '84429737000114':
                                index_max = df_invoice['gross_value'].idxmax()
                                df_invoice = df_invoice.loc[[index_max]]
                            else:
                                df_invoice = df_invoice[df_invoice['finance_category_id'] == 4471638].head(1)

                            if len(df_invoice) == 0:
                                logging.warning(f'Não foi possível identificar em qual recebível a descrição vai ser atualizada CNPJ: {cnpj}')
                                continue

                        # obtem o invoice_id para atualização
                        invoice_id = int(df_invoice['id'].values[0])

                        #criar a descrição para atualização
                        is_empty = df_invoice['description'].isna().iloc[0] or df_invoice['description'].iloc[0].strip() == ''
                        if is_empty:
                            descripion = msg
                        else:
                            descripion = df_invoice['description'].iloc[0] + '\n\r\n\r' + msg
                            logging.debug(f"Company: {empresa_id} - Descrição: {df_invoice['description']}")

                        descripion_ant = df_invoice['description'].iloc[0]
                        
                        atualizar = True
                    else:
                        alert = f"Não foi encontrado recebíveis para o CNPJ: {cnpj}"
                        logging.warning(alert)

                response = None
                if atualizar: 
                    # Requisição para atualização da cobrança
                    updateInvoice = {'description' : descripion}
                    #response = fintera.updateInvoice(contract_id, invoice_id, updateInvoice)
                    if not response:
                        atualizar = False
                    else:
                        print(f"Empresa atualizada: {cnpj} - Msg: {msg}")

                preview.append({'empresa_name':empresa_name, 
                                'empresa_id':empresa_id,
                                    'cnpj': cnpj, 
                                    'contract_id': contract_id,
                                    'invoice_id': invoice_id,
                                    'qtd_organization': numero_organizacoes,
                                    'competencia':competencia,
                                    'data_atualizacao': datetime.now(),
                                    'pedidos':numero_pedidos, 
                                    'atualizado':atualizar,
                                    'link': f"https://faturamento.fintera.com.br/contracts/{contract_id}/invoices/{invoice_id}/edit",
                                    'desc_ant': descripion_ant,
                                    'desc_new' : descripion,
                                    'alerta': alert})

                # Adicionar lock para o CNPJ e competência
                lock_manager.add_cnpj_date_lock(competencia, cnpj, msg, empresa_name, atualizar)

        #self.writterPreview(preview)

        return

    def setFileBaseMedicao(self, file):
        self.file_base = file

    def getFileBaseMedicao(self):
        return self.file_base
    
    def compareDataFramebyCNPJ(self, df1, df2, index):
        # Merge com indicador
        merged_df = df1.merge(df2, on=index, how='outer', indicator=True)
        
        # Filtrar valores que estão apenas no df1
        only_in_df1 = merged_df[merged_df['_merge'] == 'left_only']

        # Filtrar valores que estão apenas no df2
        only_in_df2 = merged_df[merged_df['_merge'] == 'right_only']

        # Resultados
        print("Present in df1 but not in df2:")
        print(only_in_df1)

        print("\nPresent in df2 but not in df1:")
        print(only_in_df2)

        only_in_df1.to_excel('outRules.xlsx')

    def writterPreview(self, preview=dict):
        # Nome do arquivo Excel
        file_name = 'preview.xlsx'

        # Convertendo CNPJ para string, se existir a coluna 'cnpj'
        if 'cnpj' in preview:
            preview['cnpj'] = [str(cnpj) for cnpj in preview['cnpj']]

        # Criar DataFrame a partir do dicionário 'preview'
        df_preview = pd.DataFrame(preview)

        # Excluir colunas onde todos os valores são NaN
        df_preview_clean = df_preview.dropna(how='all', axis=1)

        try:
            # Carregar o arquivo Excel existente, se houver
            df_existente = pd.read_excel(file_name)

            # Converter CNPJ para string no arquivo existente
            if 'cnpj' in df_existente.columns:
                df_existente['cnpj'] = df_existente['cnpj'].astype(str)

            # Excluir colunas onde todos os valores são NaN no arquivo existente
            df_existente_clean = df_existente.dropna(how='all', axis=1)

            # Concatenar os DataFrames limpos (existente + novo)
            df_combined = pd.concat([df_existente_clean, df_preview_clean], ignore_index=True)
        except FileNotFoundError:
            # Se o arquivo não existir, use apenas os novos dados
            df_combined = df_preview_clean

        # Salvar o DataFrame combinado no Excel
        df_combined.to_excel(file_name, index=False)

        return True
