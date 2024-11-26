import os
import json
from datetime import datetime

class LockManager:
    def __init__(self, filepath):
        self.filepath = self.getPath(filepath)
        self.data = self._load_data()

    def getPath(self, fileName=''):
        base_path = os.path.dirname(__file__)
        return os.path.join(base_path, fileName)
    
    def _load_data(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    if 'cnpj_dates' in data:
                        return data
                    else:
                        raise ValueError("JSON structure is invalid.")
            except (json.JSONDecodeError, ValueError):
                print("An error occurred while loading the JSON file. Initializing with default structure.")
                return {"cnpj_dates": []}
        else:
            return {"cnpj_dates": []}

    def _save_data(self):
        try:
            with open(self.filepath, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"An error occurred while saving the JSON file: {e}")

    def add_fintera_billing_account_id_date_lock(self, date_str, fintera_billing_account_id, msg='', company_name='', atualizado=0):
        fintera_billing_account_id_date_entry = {"date": date_str, "fintera_billing_account_id": fintera_billing_account_id, 'msg':msg, 'company_name':company_name, 'atualizado': atualizado}
        if fintera_billing_account_id_date_entry not in self.data["cnpj_dates"]:
            self.data["cnpj_dates"].append(fintera_billing_account_id_date_entry)
            self._save_data()

    def check_fintera_billing_account_id_date_lock(self, date_str, fintera_billing_account_id):
        # Percorrer todos os registros dentro de 'cnpj_dates'
        for entry in self.data["cnpj_dates"]:
            # Verificar se a entrada tem o CNPJ e a data correspondentes
            if entry['date'] == date_str and entry['fintera_billing_account_id'] == fintera_billing_account_id:
                return True
        return False
    
    def get_fintera_billing_account_id(self, competencia):
        # Converter a competencia para o formato string caso seja um objeto datetime
        if isinstance(competencia, datetime):
            competencia = competencia.strftime("%Y-%m")

        # Filtrar e retornar todos os CNPJs para a competência passada
        return [entry['fintera_billing_account_id'] for entry in self.data['cnpj_dates'] if entry['date'] == competencia]

    def get_receivables(self, competencia):
        # Filtrar e retornar todos os CNPJs para a competência passada
        return [entry for entry in self.data['cnpj_dates'] if entry['date'] == competencia]