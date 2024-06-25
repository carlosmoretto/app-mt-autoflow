import toml
import streamlit as st
import pandas as pd
from datetime import datetime
import time

from modules import helper, FinteraAPI, FinteraAPIException 


def show():

    st.subheader("Vamos calcular as próximas solicitações de aporte")

    selected_option = helper().get_entities_selectbox(st)
    st.write(f'Processando malote da empresa: {selected_option}')
    
    #lista com empresa ID e empresa name
    df = helper().get_entities()
    
    # Buscar o ID da empresa
    id_entity = df.loc[df["name"] == selected_option, "entity_id"].values[0]
    
    st.warning("Antes de iniciar faça os prés-requisitos: ")
    
    st.write("Gostaria de definir um saldo minimo? Caso um saldo não seja definido, o minimo será zero.")

    # Inicializa o valor mínimo da conta no estado da sessão, se ainda não estiver definido
    if 'account_min' not in st.session_state:
        st.session_state['account_min'] = 0.00
        account_min = st.session_state['account_min']

    if st.button("Sim"):
        # Ativar entrada para definir saldo mínimo
        st.session_state['definir_saldo'] = True

    # Mostra o input para definir saldo mínimo se o botão foi clicado
    if 'definir_saldo' in st.session_state and st.session_state['definir_saldo']:
        account_min = st.number_input("Definir saldo mínimo para as contas", value=float(st.session_state['account_min']), format="%.2f")
        st.session_state['account_min'] = account_min  # Atualizar o valor no estado da sessão
    else:
        account_min = st.session_state['account_min']  # Usar o valor padrão ou o já definido

    confirmed = st.button("Está tudo certo para iniciar?")
    if confirmed:
        # Configurações da API
        BASE_URL = 'https://financeiro.fintera.com.br'
        TOKEN = st.secrets.api.FINTERA_FINA_25

        # Inicializar a API
        api = FinteraAPI(BASE_URL, TOKEN)
        
        # calculo de aporte para next_days 
        next_days = 10

        with st.spinner('Carregando contas a pagar...'):
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

        list_banks = df["payable_account.expected_deposit_account_id"].unique()
    
        st.subheader("Vamos fazer o calculo de aporte para cada conta bancária existente.")
        st.write(F"Você tem {len([x for x in list_banks if x != 0])} contas para o calculo.")
        
        df['payable_account.due_date'] = pd.to_datetime(df['payable_account.due_date'])
        df['day_year_month'] = df['payable_account.due_date'].dt.to_period('D')

        df["payable_account.total_amount"] = df["payable_account.total_amount"].astype(float)
        df["payable_account.amount"] = df["payable_account.amount"].astype(float)
        day_month_sales = df.groupby("day_year_month")["payable_account.amount"].sum().reset_index()
        day_month_sales["payable_account.amount"] = day_month_sales["payable_account.amount"].apply(lambda x: f"{x:.2f}")
        day_month_sales["day_year_month"] = day_month_sales["day_year_month"].dt.to_timestamp()

        for bank in list_banks:
            #Fazer a consulta para buscar os dados bancários
            if bank > 0:
                with st.spinner('Carregando dados das contas bancárias...'):
                    bank_res = api.get_deposit_accounts(id_entity, bank)
                
                bank_df = pd.DataFrame(bank_res)

                deposit_account_calculated_balance = float(0.00)

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

                    st.data_editor(day_month_sales,
                                   column_config={
                                        "day_year_month": st.column_config.DateColumn(
                                            "Data",
                                            format="DD/MM/YYYY"
                                        ),"payable_account.amount": st.column_config.NumberColumn(
                                            "Contas a Pagar",
                                            format="%.2f",
                                        ),"aporte": st.column_config.NumberColumn(
                                            "Valor a Aportar",
                                            format="%.2f",
                                        ),"novo_saldo": st.column_config.NumberColumn(
                                            "Saldo",
                                            format="%.2f",
                                        ),                                        
                                   })