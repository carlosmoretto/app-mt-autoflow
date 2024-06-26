import streamlit as st
from streamlit_option_menu import option_menu
from authentication.login import authenticate, logout
from my_pages import home, assess_capital_requirements, billing_measurements, contracts_summary

#from my_pages import home, billing_measurements, client_contract_termination, bank_batch_processing, assess_capital_requirements

menu_style = {
                "container": {"padding": "0!important", "background-color": "#f0f0f0"},
                "icon": {"color": "orange", "font-size": "25px"}, 
                "nav-link": {
                    "font-size": "13px",
                    "text-align": "left",
                    "margin": "0px",
                    "padding": "10px",
                    "color": "black",
                },
                "nav-link-selected": {"background-color": "#a1dbfb", "font-weight": "normal"},
            }

st.set_page_config(layout="wide", page_title="MT ASSESSORIA", page_icon=":smiley:", initial_sidebar_state="auto")

def main():
    # Verifica se o usuário está logado
    if not st.session_state.get('authenticated', False):
        # Usuário não está logado, mostrar o formulário de login
        if authenticate():
            # Após login, mostra o conteúdo principal
            show_main_content()
        else:
            # Continua mostrando o formulário de login
            st.sidebar.warning("Por favor, faça login para acessar o aplicativo.")
    else:
        # Usuário está logado, mostra o conteúdo principal
        show_main_content()
        if st.session_state.get('authenticated', True):
            if st.sidebar.button("Logout"):
                logout()            
            

def show_main_content():
    """Função para exibir o conteúdo principal do aplicativo."""
    # Sidebar menu without explicit input
    with st.sidebar:
        selected_main = option_menu(
            menu_title="Menu",
            options=["Home", "Nexaas"],
            icons=["house", "bi-tools"],
            menu_icon="cast",
            default_index=0,
            #styles=menu_style
        )

    if selected_main == "Home":
        home.show()
    else:
        if selected_main == "Nexaas":
            with st.sidebar:
                selected_sub = option_menu(
                    menu_title="Nexaas",
                    options=["Lançamento de Medição", "Baixar Malote", "Calculo de Rescisão", "Calculo de Aporte", "Contratos AI"],
                    icons=["bi-cash-coin", "bi-cloud-download", "bi-x", "bi-cash-coin", "bi-file-earmark"],
                    menu_icon="bi-tools",
                    default_index=0,
                    #styles=menu_style
                )

            if selected_sub == "Lançamento de Medição":
                billing_measurements.show()
            # elif selected_sub == "Baixar Malote":
            #     bank_batch_processing.show()
            # elif selected_sub == "Calculo de Rescisão":
            #     client_contract_termination.show()
            elif selected_sub == "Calculo de Aporte":
                assess_capital_requirements.show()
            elif selected_sub == "Contratos AI":
                contracts_summary.show()                

if __name__ == '__main__':
    main()