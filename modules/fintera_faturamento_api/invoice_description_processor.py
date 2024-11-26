import logging
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar

from modules.fintera_faturamento_api.fintera_api import Fintera
from modules.fintera_faturamento_api.helper import Helper
from modules.fintera_faturamento_api.faturamento_lock import LockManager


class InvoiceDescriptionProcessor:
    
    def __init__(self):
      logging.basicConfig(
          filename="atualizacao.log",
          level=logging.INFO,
          encoding='utf-8',
          format="%(asctime)s - %(levelname)s - %(message)s",
          datefmt="%Y-%m-%d %H:%M:%S"
      )
      self.all_medicao_file = None

    def set_medicao_file(self, data):
        self.all_medicao_file = data

    def get_data_base_medicao(self):
        """
        Método para obter os dados base de medição.
        Deve ser implementado conforme a fonte de dados utilizada.
        """
        # Implementar conforme necessário
        return pd.DataFrame(self.all_medicao_file)
    
    def get_prepared_collection(self):
        """
        Retorna um df com todas as descrições que precisam ser atualizadas
        Será usado no preview
        """
        all_pedicao = self.get_data_base_medicao()
        competencia = self.extract_competencia(all_pedicao)

        # # REMOVER APÓS VALIDAÇÃO
        # competencia_date = datetime.strptime("2024-11-01", "%Y-%m-%d")
        # competencia = competencia_date.strftime("%Y-%m")

        competencia_filter_ini, competencia_filter_fim = self.calculate_competencia_filters(competencia)

        #Chama a class Fintera
        fintera = self.get_fintera()
        fintera.setEntity("Filial")
        supplier = fintera.getTokens()
        supplier_filial = supplier["Filial"][1]

        # remove campos null
        valid_billing_ids = all_pedicao['fintera_billing_account_id'].dropna()
        # converte para int
        valid_billing_ids = valid_billing_ids.astype(int)
        # uma lista única
        valid_billing_ids = valid_billing_ids.unique()

        _list_final = []

        for billing_id in valid_billing_ids.tolist():
            
            row_to_append = dict()

            row_to_append["empresa_title"] = None
            row_to_append["billing_id"] = billing_id
            row_to_append["contract_id"] = None
            row_to_append["invoice_id"] = None
            row_to_append["error"] = 0

            # Calcula a quantidade de pedidos e organizações
            qtd_pedidos, qtd_organizacao = self.calculate_orders_and_organizations(billing_id, all_pedicao)
            description = f"Quantidade de pedidos {competencia}: {qtd_pedidos}"
            row_to_append["description_to_update"] = description
            
            # verificar se existe contrato
            contracts = fintera.getContract(billing_id)
            if not contracts or not contracts.get("contracts"):
                alert = 'Fintera não encontrou contratos para empresa com id'
                logging.warning(alert)
                row_to_append["alert"] = alert
                row_to_append["error"] = 1
                _list_final.append(row_to_append)
                continue

            #filtra apenas por contratos da filial e ativos
            filter_contract = self.get_filtered_contracts(contracts, supplier_filial)
            if len(filter_contract) == 0:
                alert = 'Não foi encontrado contratos ativos ou que pertencem a MYFC Filial para esta companhia'
                row_to_append["alert"] = alert
                row_to_append["error"] = 1
                _list_final.append(row_to_append)
                continue

            contract = filter_contract[0]
            row_to_append["contract_id"] = contract['id']
            row_to_append["empresa_title"] = contract['title']

            # Buscar os recebíveis do contrato
            faturamentos = fintera.getReceivables(contract['id'], self.get_filter_to_receivables(competencia_filter_ini, 3))
            if not faturamentos or not faturamentos[0].get('receivables'):
                alert = 'Não foi encontrado faturamentos para a empresa.'
                row_to_append["alert"] = alert
                row_to_append["error"] = 1
                _list_final.append(row_to_append)
                continue
            
            invoice_list = [r['invoice'] for r in faturamentos[0]['receivables'] if r['invoice']]

            df_invoice = pd.DataFrame(invoice_list)
            df_invoice['estimated_issue_date'] = pd.to_datetime(df_invoice['estimated_issue_date'], dayfirst=True)
            df_invoice = df_invoice[
                  (df_invoice['estimated_issue_date'] >= competencia_filter_ini) &
                  (df_invoice['estimated_issue_date'] <= competencia_filter_fim)
            ]
            
            if df_invoice.empty:
                alert = f'Sem cobranças identificadas para esta empresa.'
                row_to_append["alert"] = alert
                row_to_append["error"] = 1
                _list_final.append(row_to_append)
                continue

            if len(df_invoice) > 1:
                logging.warning(f'Mais de uma invoice para ser faturada no CNPJ.')
                if billing_id == 24449:
                    index_max = df_invoice['gross_value'].idxmax()
                    df_invoice = df_invoice.loc[[index_max]]
                else:
                    df_invoice = df_invoice[df_invoice['finance_category_id'] == 4471638].head(1)

                if df_invoice.empty:
                    alert = f'Não foi possível identificar em qual recebível a descrição vai ser atualizada CNPJ.'
                    row_to_append["alert"] = alert
                    row_to_append["error"] = 1
                    _list_final.append(row_to_append)
                    continue
                    
            
            invoice_id = int(df_invoice['id'].values[0])
            row_to_append['invoice_id'] = invoice_id
            current_description = df_invoice['description'].iloc[0] if not df_invoice['description'].isna().iloc[0] else ''
            is_empty = current_description.strip() == ''

            description = description if is_empty else current_description + '\n\r\n\r' + description
            description_ant = current_description

            row_to_append['new_description'] = description
            row_to_append['old_description'] = description_ant
            row_to_append['link'] = f"https://faturamento.fintera.com.br/contracts/{contract['id']}/invoices/{invoice_id}/edit"

            _list_final.append(row_to_append)

        return _list_final

    def get_fintera(self):
        return Fintera()

    def extract_competencia(self, all_medicao_file):
        """
        Extrai a competência a partir dos dados de medição.

        :param all_medicao_file: DataFrame com os dados de medição.
        :return: Competência no formato 'YYYY-MM'.
        """
        competencia_array = all_medicao_file['Mês'].unique()
        if len(competencia_array) == 0:
            logging.error("Nenhuma competência encontrada nos dados de medição.")
            raise ValueError("Nenhuma competência encontrada nos dados de medição.")
        competencia_date = competencia_array[0]
        if not isinstance(competencia_date, datetime):
            competencia_date = datetime.strptime(competencia_date, "%Y-%m-%d")
        return competencia_date.strftime("%Y-%m")
    
    def calculate_orders_and_organizations(self, billing_id, all_medicao_file):
        """
        Calcula o número de pedidos e organizações para um billing ID.

        :param billing_id: ID de cobrança.
        :param all_medicao_file: DataFrame com os dados de medição.
        :return: Tupla com número de pedidos e organizações.
        """
        billing_id = int(billing_id)
        numero_pedidos = all_medicao_file.loc[
            all_medicao_file['fintera_billing_account_id'] == billing_id, 'Qtd de pedidos'
        ].sum()
        numero_organizacoes = all_medicao_file.loc[
            all_medicao_file['fintera_billing_account_id'] == billing_id, 'cnpj'
        ].nunique()
        return int(numero_pedidos), numero_organizacoes
    
    def calculate_competencia_filters(self, competencia_str):
        """
        Calcula as datas de início e fim da competência.

        :param competencia_str: Competência no formato 'YYYY-MM'.
        :return: Tupla com as datas de início e fim da competência.
        """
        competencia_date = datetime.strptime(competencia_str, "%Y-%m")
        competencia_filter_ini = competencia_date + relativedelta(months=1)
        ultimo_dia = calendar.monthrange(competencia_filter_ini.year, competencia_filter_ini.month)[1]
        competencia_filter_fim = competencia_filter_ini.replace(day=ultimo_dia)
        return competencia_filter_ini, competencia_filter_fim
    
    def get_filtered_contracts(self, contracts, supplier_filial):
        """
        Função preparada para adaptação, caso seja necessário filtrar os contratos de outras maneiras
        """
        return [r for r in contracts['contracts'] if r['supplier_id'] == supplier_filial and r['status'] == 'established']
        
    def get_filter_to_receivables(self, data, meses=0):
        """
        Vai retornar o filtro preparado para chamar a API de recebíveis da Fintera
        """
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
            "state": "to_emit" #apenas cobranas para emissão
        }
    
    def preview_description(self):
        """
        Função vai retornar apenas uma lista de dicionários para ser visualizada previamente
        """
        return self.get_prepared_collection()
    
    def update_invoice_descriptions(self):
        """
        Função responsável por atualizar a invoice com as descrições de quantidade de pedidos
        """
        
        lock_manager = LockManager('locks.json')

        fintera = self.get_fintera()
        fintera.setEntity("Filial")

        all_pedicao = self.get_data_base_medicao()
        competencia = self.extract_competencia(all_pedicao)

        collection_to_updade = pd.DataFrame(self.get_prepared_collection())

        # Apenas lista sem erros
        collection_to_updade = collection_to_updade[collection_to_updade['error'] == 0]

        # filtrar os ids de cobrança
        if len(lock_manager.get_fintera_billing_account_id(competencia)) > 0:
            collection_to_updade = collection_to_updade[~collection_to_updade['billing_id'].isin(lock_manager.get_fintera_billing_account_id(competencia))]

        for index, billing in collection_to_updade.iterrows():

            atualizado = 0

            if not lock_manager.check_fintera_billing_account_id_date_lock(competencia, billing['billing_id']):

                if not billing['error']:
                    # print(f"{billing['billing_id']} - Para Atualizar")
                    updateInvoice = {'description' : billing['new_description']}
                    response = fintera.updateInvoice(int(billing['contract_id']), int(billing['invoice_id']), updateInvoice)

                    if response:
                        atualizado = 1

                lock_manager.add_fintera_billing_account_id_date_lock(competencia, billing['billing_id'], 
                                                billing['description_to_update'], 
                                                billing['empresa_title'], atualizado)

        return competencia