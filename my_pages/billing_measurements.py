
import streamlit as st
import pandas as pd
from io import StringIO
from modules import Model


def show():

    m = Model()
    
    uploaded_file = st.file_uploader("Escolha o arquivo de medição")
    if uploaded_file is not None:
        # To read file as bytes:
        
        m.setFileBaseMedicao(m.getHelper().planilha_para_lista_dicionarios(uploaded_file))
        
        with st.container():
            st.write("Visualize com cuidado cada tabela para conferência")

        with st.container():
            st.warning("ATENÇÃO - Empresa sem regra de cobrança adicional cadastrada", icon="⚠️")

            # Cria uma tabela com os dados e formatação
            colunas, data = m.prepareCollectionData(m.getEntitiesOnlyRule(), ['Conta - Organização - CNPJ', 'Mês',"CNPJ Cobrança", 
                                                                            'Qtd de pedidos', 'Pedido Limite', 'Pedido Add'])    
            df = pd.DataFrame(data, columns=colunas)

            st.data_editor(
                df,
                column_config={
                    "Qtd de pedidos": st.column_config.NumberColumn(
                        format="%.0f"
                    ),
                    "Total Add": st.column_config.NumberColumn(
                        format="%.2f",
                    ),
                    "Mês": st.column_config.DateColumn(
                        format="DD/MM/YYYY",
                    ),
                    "Pedido Add": st.column_config.NumberColumn(
                        "R$ Pedido Add",
                        format="%.2f",
                    ),
                },
            )
            
        # Abaixo todos os clientes
        with st.container():
            st.info("Abaixo todos os clientes")
            # Cria uma tabela com os dados e formatação
            colunas, data = m.prepareCollectionData(m.getEntities(), ['Conta - Organização - CNPJ', 'Mês', "CNPJ Cobrança", 'Qtd de pedidos', 'Pedido Limite', 'Pedido Add'] )    
            df = pd.DataFrame(data, columns=colunas)
            st.data_editor(
                df,
                column_config={
                    "Qtd de pedidos": st.column_config.NumberColumn(
                        format="%.0f"
                    ),
                    "Total Add": st.column_config.NumberColumn(
                        format="%.2f",
                    ),
                    "Mês": st.column_config.DateColumn(
                        format="DD/MM/YYYY",
                    ),
                    "Pedido Add": st.column_config.NumberColumn(
                        "R$ Pedido Add",
                        format="%.2f",
                    ),
                    "Qtd de pedidos": st.column_config.ProgressColumn(
                        "Sales volume",
                        help="The sales volume in USD",
                        format="%f",
                        min_value=0,
                        max_value=6500,
                    ),
                },
            )
            
        with st.container():
            st.info("Empresas que excederam a limitação de pedidos")

            # Cria uma tabela com os dados e formatação   
            colunas, data = m.prepareCollectionData(m.getEntitiesAddValue(), ['Conta - Organização - CNPJ', 'Mês',"CNPJ Cobrança", 'Qtd de pedidos', 'Pedido Limite', 'Pedido Add', "Total Add"] )

            df = pd.DataFrame(data, columns=colunas)
            
            st.data_editor(
                df,
                column_config={
                    "Qtd de pedidos": st.column_config.NumberColumn(
                        format="%.0f"
                    ),
                    "Total Add": st.column_config.NumberColumn(
                        format="%.2f",
                    ),
                    "Mês": st.column_config.DateColumn(
                        format="DD/MM/YYYY",
                    ),
                    "Pedido Limite": st.column_config.NumberColumn(
                        format="%.0f",
                    ),
                    "Pedido Add": st.column_config.NumberColumn(
                        "R$ Pedido Add",
                        format="%.2f",
                    ),
                },
            )
            
            if st.button('Lançar medições'):
                
                #exec = m.process()
                exec = True
                if exec:
                    st.success("Medições lançadas com sucesso")
                else:
                    st.error('Erro ao executar o lançamento')