
import streamlit as st
import pandas as pd
from modules import helper, FinteraAPI, FinteraAPIException, helper
from datetime import datetime

def show():
    st.title("Malote Bancário")
    st.write("Esta página vai ser utilizada para baixar os malotes bancários.")

    selected_option = helper().get_entities_selectbox(st)

    st.write(f'Processando malote da empresa: {selected_option}')
    
    #lista com empresa ID e empresa name
    df = helper().get_entities()
    
    # Buscar o ID da empresa
    id_entity = df.loc[df["name"] == selected_option, "entity_id"].values[0]
    
    st.write(f'Empresa ID: {id_entity}')
    
    
    st.warning("Entes de iniciar é preciso que as contas estejam conciliadas até a data atual.")
    confirmed = st.button("Está tudo certo para iniciar?")
    if confirmed:
    
        # Configurações da API
        BASE_URL = 'https://financeiro.fintera.com.br'
        TOKEN = st.secrets.api.FINTERA_FINA_25

        # Inicializar a API
        api = FinteraAPI(BASE_URL, TOKEN)
        
        
        # calculo de aporte para next_days 
        next_days = 10
        account_min = 2000
        
        result = api.list_payable_accounts(id_entity, {"search[due_date_gte]":"22/06/2024", 
                                                    "search[due_date_lte]":"15/07/2024"
                                                    })

        df = pd.json_normalize(result, meta=["id", "entity_id"])

        df = df[["payable_account.entity_id", 
                    "payable_account.status_name", 
                    'payable_account.due_date', 
                    "payable_account.amount", 
                    "payable_account.total_amount",
                    "payable_account.expected_deposit_account_id",
                    "payable_account.person_id"]]    
        df['payable_account.expected_deposit_account_id'] = df['payable_account.expected_deposit_account_id'].fillna(0).astype(int)
        #import pdb; pdb.set_trace()
        list_banks = df["payable_account.expected_deposit_account_id"].unique()
    
        st.subheader("Vamos fazer o calculo de aporte para cada conta bancária existente.")
        st.write(F"Você tem {len([x for x in list_banks if x != 0])} contas para o calculo.")

        df['payable_account.due_date'] = pd.to_datetime(df['payable_account.due_date'])
        df['day_year_month'] = df['payable_account.due_date'].dt.to_period('D')
        
        df["payable_account.total_amount"] = df["payable_account.total_amount"].astype(float)
        df["payable_account.amount"] = df["payable_account.amount"].astype(float)
        day_month_sales = df.groupby("day_year_month")["payable_account.amount"].sum().reset_index()
        day_month_sales["payable_account.amount"] = day_month_sales["payable_account.amount"].apply(lambda x: f"{x:.2f}")

        date_range = helper().generate_date_range('2024-06-22', '2024-07-15')
        for bank in list_banks:
            #Fazer a consulta para buscar os dados bancários
            if bank > 0:
                bank_res = api.get_deposit_accounts(id_entity, bank)
                bank_df = pd.DataFrame(bank_res)

                if "deposit_account" in bank_df.columns:
                    # Criando uma nova coluna 'account_name' baseada na chave 'name' do dicionário em 'deposit_account'
                    deposit_account_name = bank_df['deposit_account']['name']
                    deposit_account_calculated_balance = float(bank_df['deposit_account']['calculated_balance'])
                    
                    st.write(F"1. Buscando informações da conta: {deposit_account_name}")
                    st.write(F"2. Saldo atual: {helper().get_number(deposit_account_calculated_balance)}")
                    
                    saldo_novo = 0
                    saldo_ant = 0
                    first = True

                    for index, day_payable_account in day_month_sales.iterrows():
                        # import pdb;pdb.set_trace()
                        amount = float(day_payable_account['payable_account.amount'])
                        if first:
                            first = False
                            day_result = deposit_account_calculated_balance - amount
                            saldo_novo = day_result
                        else:
                            saldo_novo -= amount
                            
                        if saldo_novo < account_min:
                            day_month_sales.at[index, "aporte"] = (saldo_novo*-1) + account_min
                            saldo_novo += day_month_sales.at[index, "aporte"]
                        else:
                            day_month_sales.at[index, "aporte"] = 0

                        day_month_sales.at[index, "novo_saldo"] = saldo_novo
                        saldo_ant = saldo_novo
    
                    st.data_editor(day_month_sales)