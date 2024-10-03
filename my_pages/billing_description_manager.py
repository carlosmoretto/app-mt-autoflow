import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime
import time

from modules import Model
from modules.fintera_faturamento_api.faturamento_lock import LockManager

def show():

    @st.cache_data
    def convert_excel(df):
        # Criar um buffer em memória para armazenar o arquivo Excel
        output = BytesIO()
        
        # Salvar o DataFrame no buffer como Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        # Posicionar o ponteiro no início do buffer
        output.seek(0)
        
        return output


    st.title("Atualização de descrição de cobranças! :sunglasses:")

    st.subheader("""
            Para que tudo funcione corretamente, lembre-se de que:\n
            1 - O cliente precisa ter um contrato ativo no sistema e o contrato deve ser com a MyFinance Filial.\n
            2 - Contrato precisa ter lançamentos de mensalidades (recorrência).\n
            3 - A categoria da receita deve ser [4471638] 2018 - Receitas Nacionais / Assinatura de Produto.\n
            4 - Em caso de erro no meio da execução, não se preocupe, apenas os pendentes serão atualizados.
            """)

    m = Model()
    uploaded_file = st.file_uploader("Escolha o arquivo de medição")

    if uploaded_file is not None:
        # Converter o arquivo de medição para a lista de dicionários
        m.setFileBaseMedicao(m.getHelper().planilha_para_lista_dicionarios(uploaded_file))

        with st.container():
            st.success("Aconselhado: Visualize por um arquivo Excel antes de atualiza")
            if st.button("Carregar a pré-visualização"):
                with st.spinner('Aguarde o arquivo ser gerado...'):

                    # Obter a data atual e formatar o nome do arquivo
                    current_date = datetime.now().strftime("%d-%m-%Y")
                    name_file = f"descriction_{current_date}.xlsx"

                    # Gerar a pré-visualização (substitua pela função real)
                    preview = pd.DataFrame(m.previewDescriptions())

                    # Converter o DataFrame em Excel no buffer
                    file = convert_excel(preview)
                    st.success("Arquivo de pré-visualização gerado com sucesso!")
                    # Download do arquivo Excel
                    st.download_button(label="Download da pre-visualização",
                                    data=file, 
                                    file_name=name_file, 
                                    mime="application/vnd.ms-excel")

            st.warning("Não aconselhado: Atualização direta :heavy_exclamation_mark:")
            if st.button("Atualizar descrição das cobranças"):
                with st.spinner('Aguarde enquanto o faturamento é atualizado...'):
                    
                    m.processDescription()

                    lock = LockManager('locks.json')
                    if len(lock.get_receivables(datetime(2024, 9, 1))) > 1:
                        df_receivables = pd.DataFrame(lock.get_receivables(datetime(2024, 9, 1)))

                        st.dataframe(df_receivables)

if __name__ == '__main__':
    show()