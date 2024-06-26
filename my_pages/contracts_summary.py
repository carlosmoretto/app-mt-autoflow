import streamlit as st
from modules import helper, FinteraAPI, FinteraAPIException, sumarizar_texto
from utils import extrair_texto_de_pdf

def show():

    st.title("Resumo de contratos para rescisão")
    
    st.subheader("Entendimento prático de contratos usando AI")
    
    """
    st.write("Para iniciar, selecione a empresa")
    selected_option = helper().get_entities_selectbox(st)
    #lista com empresa ID e empresa name
    df = helper().get_entities()
    # Buscar o ID da empresa
    id_entity = df.loc[df["name"] == selected_option, "entity_id"].values[0]
    
    #buscar clientes da filial e colocar em um select
    """
    st.write("Para iniciar, selecione o contrato que deseja carregar")
    # Permitir que o usuário carregue um arquivo PDF
    uploaded_file = st.file_uploader("Carregue seu contrato em PDF aqui", type=["pdf"])      
    if uploaded_file is not None:
        # Extrair texto do PDF carregado
        texto_contrato = extrair_texto_de_pdf(uploaded_file)
        with st.spinner("Trabalhando com seu contrato..."):
            # Sumarizar o texto extraído
            resumo = sumarizar_texto(st.secrets.api.OPENAI, texto_contrato)
            # Exibir o resumo
            st.write(resumo['choices'][0]['message']['content'])