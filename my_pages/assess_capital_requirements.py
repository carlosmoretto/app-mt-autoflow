import toml
import streamlit as st
import pandas as pd
from datetime import datetime
import time
import re

from modules import helper, FinteraAPI, FinteraAPIException


def show():

    st.subheader("Vamos calcular as próximas solicitações de aporte")

    selected_option = helper().get_entities_selectbox(st)
    st.write(f'Processando malote da empresa: {selected_option}')
    
    #lista com empresa ID e empresa name
    df = helper().get_entities()
    
    # Buscar o ID da empresa
    id_entity = df.loc[df["name"] == selected_option, "entity_id"].values[0]
    
    st.warning("Antes de iniciar faça os prés-requisitos: \n1. Conciliação deve estar em dia.\n2. Todas as despesas a vencer precisam ter conta bancária informada")
    
    st.write("Gostaria de definir um saldo minimo? (Caso o saldo minimo não seja definido, o minimo zero)")

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

    contas_receber = st.checkbox("Considerar contas a receber")
    
    confirmed = st.button("Está tudo certo para iniciar?")
    if confirmed:
        # Configurações da API
        BASE_URL = 'https://financeiro.fintera.com.br'
        TOKEN = st.secrets.api.FINTERA_FINA_25

        # Inicializar a API
        api = FinteraAPI(BASE_URL, TOKEN)
        
        group_by = []        
        with st.status("Downloading..."):
            st.write("Procurando contas a pagar...")
            type = "payable_accounts"
            result = api.list_payable_accounts(id_entity, type, {"search[due_date_gte]":"01/07/2024", 
                                                        "search[due_date_lte]":"05/07/2024"})
            df_agruped = prepare_counts(result, "payable_account")
            
            group_by.append("payable_account.amount")
            
            if contas_receber:
                st.write("Procurando contas a receber...")
                df_agruped_pagar = df_agruped
                type = "receivable_accounts"
                result = api.list_payable_accounts(id_entity, type, {"search[due_date_gte]":"01/07/2024", 
                                                        "search[due_date_lte]":"05/07/2024"})
                df_agruped = prepare_counts(result, "receivable_account")
                group_by.append("receivable_account.amount")

                df_agruped = pd.merge(df_agruped_pagar, df_agruped, on=["due_date", "expected_deposit_account_id"], how='outer')
            
                df_agruped['payable_account.amount'] = df_agruped['payable_account.amount'].fillna(0.0).astype(float)
        
        if 'receivable_account.amount' in df_agruped.columns:
            df_agruped['receivable_account.amount'] = df_agruped['receivable_account.amount'].fillna(0.0).astype(float)
        
        st.subheader("Executando calculo de aporte para cada conta bancária existente. :rocket:")

        bank_list = df_agruped["expected_deposit_account_id"].unique()
        
        saldo_total_inicial = 0
        
        i = 0
        for bank in bank_list:
            i += 1
            if bank > 0:
                #consulta o saldo inicial de cada conta
                with st.spinner('Carregando dados das contas bancárias...'):
                    bank_res = api.get_deposit_accounts(id_entity, bank)                

                bank_df = pd.DataFrame(bank_res)
                
                deposit_account_calculated_balance = float(0.00)
                if "deposit_account" in bank_df.columns:
                    deposit_account_name = bank_df['deposit_account']['name']
                    deposit_account_calculated_balance = float(bank_df['deposit_account']['calculated_balance'])
                    saldo_total_inicial += deposit_account_calculated_balance
                    
                    st.write(F"1. Buscando informações da conta: {deposit_account_name}")
                    st.write(F"2. Saldo atual: {helper().get_number(deposit_account_calculated_balance)}")
                    
                    df_filtered = df_agruped[df_agruped["expected_deposit_account_id"] == bank]
                    df = creat_capila_support(df_filtered, account_min, deposit_account_calculated_balance)

                    st.write("Valor total de aportes para o perído: "+ helper().get_number(df['aporte'].sum()))
                    create_table(df, f"data_editor_{i}")
        
        if len(bank_list) > 0:
            st.write("3. Totalizador geral de aportes....")
            df = df_agruped.groupby("due_date").sum(group_by).reset_index()
            df = creat_capila_support(df, account_min, saldo_total_inicial)

            st.write("Valor total de aportes para o perído: "+ helper().get_number(df['aporte'].sum()))
            create_table(df, "data_editor_summery")

            create_summary(df)

def prepare_counts(results, type_str):
    
    df = pd.json_normalize(results, meta=["id", "entity_id"])
    
    index = ["entity_id", 
            "status_name", 
            'due_date', 
            "amount", 
            "total_amount",
            "expected_deposit_account_id",
            "person_id"]

    # simplifica a lista
    df = df[[f'{type_str}.{x}' for x in index]]

    # converte colunas vazias para zero
    df['expected_deposit_account_id'] = df[f'{type_str}.expected_deposit_account_id'].fillna(0)
    df['expected_deposit_account_id'] = df['expected_deposit_account_id'].infer_objects()

    # converte o campo vencimento para datetime
    df[f'{type_str}.due_date'] = pd.to_datetime(df[f'{type_str}.due_date'])
    
    # campo para agrupamento
    df['due_date'] = pd.to_datetime(df[f'{type_str}.due_date'])
    
    # Converter para float
    df[f'{type_str}.amount'] = df[f'{type_str}.amount'].astype(float)
    df[f'{type_str}.total_amount'] = df[f'{type_str}.total_amount'].astype(float)

    df_agruped = df.groupby(['due_date', 'expected_deposit_account_id'])[f'{type_str}.amount'].sum().reset_index()

    return df_agruped

def creat_capila_support(df, min_bank_balance, bank_balance):
    # Assegure que o DataFrame é uma cópia para não alterar o original fora da função
    df = df.copy()

    # Inicializar as colunas 'aporte' e 'novo_saldo' com tipos apropriados
    df['aporte'] = pd.Series(dtype='float')
    df['novo_saldo'] = pd.Series(dtype='float')
    
    saldo_novo = bank_balance

    for index, row in df.iterrows():
        amount = float(row['payable_account.amount'])
        receivable_accounts_amount = float(row.get('receivable_account.amount', 0.0))
        
        saldo_novo -= (amount - receivable_accounts_amount)

        if saldo_novo < min_bank_balance:
            aporte_necessario = min_bank_balance - saldo_novo
            df.loc[index, 'aporte'] = aporte_necessario
            saldo_novo += aporte_necessario
        else:
            df.loc[index, 'aporte'] = 0.0

        df.loc[index, 'novo_saldo'] = saldo_novo
    
    df = df.drop(["expected_deposit_account_id"], axis=1)
    
    return df

def create_table(df, key_form):

    df['aporte'] = df['aporte'].map(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    if 'receivable_account.amount' in df.columns:
        df['receivable_account.amount'] = df['receivable_account.amount'].map(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    df['payable_account.amount'] = df['payable_account.amount'].map(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    df['novo_saldo'] = df['novo_saldo'].map(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    st.dataframe(df,
                column_config={
                    "due_date": st.column_config.DateColumn(
                        "Data",
                        format="dddd, DD/MM/YYYY",
                        width=None
                    ),"receivable_account.amount": st.column_config.TextColumn(
                        "A receber",
                    ),"payable_account.amount": st.column_config.TextColumn(
                        "A Pagar",
                    ),"aporte": st.column_config.TextColumn(
                        "Valor a Aportar",
                    ),"novo_saldo": st.column_config.TextColumn(
                        "Saldo",
                    )})
    
def create_summary (df):
    st.subheader("Processo de Calculo Feito com Sucesso:")
    
    if st.button("Gostaria de enviar por email?"):
        # Solicita entrada do usuário
        email = st.text_input("Email", placeholder="Digite o email...")

        if email:  # Verifica se alguma coisa foi digitada
            if validar_email(email):
                st.success("Email válido!")
            else:
                st.error("Email inválido. Por favor, digite um email válido.")
        else:
            st.info("Por favor, digite um email.")

def validar_email(email):
    # Regex para validar email
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if re.match(pattern, email):
        return True
    return False