import pandas as pd
import locale
import platform
import sys

class helper:
    
    def get_entities(self):

        entities = [           
            {"entity_id": 14210, "name": "Myfinance Consultoria e Informatica S.A. Matriz - RJ"},
            {"entity_id": 33984, "name": "Myfinance Consultoria e Informatica S.A. Filial - SP"},
            {"entity_id": 34524, "name": "Contabilone Software de Gestao Contabil e Fiscal LTDA."},
            {"entity_id": 10590, "name": "Webmídia"},
            {"entity_id": 34633, "name": "FGP Desenvolvimento de Software LTDA"}
        ]

        return pd.DataFrame(entities)

    def get_entities_selectbox(self, st):
        """
            Returna um selectbox que pode ser usado em todo o projeto
        """
        hp = self.get_entities()
        options = hp["name"]
        return st.selectbox('Escolha uma empresa:', options)
    
    def generate_date_range(self, start_date, end_date):
        """
        Gera uma lista de datas entre start_date e end_date.

        Parâmetros:
        start_date (str): Data de início no formato 'YYYY-MM-DD'.
        end_date (str): Data final no formato 'YYYY-MM-DD'.

        Retorna:
        list: Lista de datas entre start_date e end_date.
        """
        # Convertendo as datas de string para datetime
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Gerando o intervalo de datas
        date_range = pd.date_range(start=start, end=end)
        
        # Convertendo o intervalo de datas para uma lista de strings no formato 'YYYY-MM-DD'
        date_list = date_range.strftime('%Y-%m-%d').tolist()
        
        return date_list
    
    def get_number (self, value):
        value = float(value)  # Convertendo para float

        try:
            # Identificar o sistema operacional
            os_type = platform.system()

            # Configuração de locale para usar ponto como separador de milhar e vírgula para decimal
            if os_type == 'Linux':
                locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
            elif os_type == 'Windows':
                locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
        except locale.Error:
            locale.setlocale(locale.LC_ALL, '')  # Usar locale padrão do sistema se falhar

        # Formatando o número
        formatted_number = locale.format_string("%.2f", value, grouping=True)

        # Retornando o número formatado
        return formatted_number