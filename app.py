import streamlit as st
from streamlit_option_menu import option_menu
import json
import os

from authentication.login import authenticate, logout
from my_pages import home, assess_capital_requirements, billing_measurements, billing_description_manager, autoflow_manager_menu

# Função para carregar as configurações do menu de um arquivo JSON
def load_menu_config():
    config_path = 'config/menus.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Ordenar menus e submenus
        data['menus'] = sorted(data['menus'], key=lambda x: x.get('order', 999))
        for menu in data['menus']:
            if 'submenu' in menu:
                menu['submenu'] = sorted(menu['submenu'], key=lambda x: x.get('order', 999))
        return data

def main():
    st.set_page_config(layout="wide", page_title="AUTOFLOW", page_icon=":smiley:", initial_sidebar_state="auto")
    
    # Verifica se o usuário está logado
    if not st.session_state.get('authenticated', False):
        if authenticate():
            display_menu()
        else:
            st.sidebar.warning("Por favor, faça login para acessar o aplicativo.")
    else:
        display_menu()
        if st.sidebar.button("Logout"):
            logout()

def display_menu():
    with st.sidebar:
        menus = load_menu_config()
        selected_main = option_menu(
            menu_title="Menu Principal",
            options=[menu['title'] for menu in menus['menus']],
            icons=[menu['icon'] for menu in menus['menus']],
            menu_icon="cast",
            default_index=0
        )

    # Encontrar o menu e submenu selecionados e exibir conteúdo na área principal
    for menu in menus['menus']:
        if selected_main == menu['title']:
            if 'submenu' in menu:
                with st.sidebar:
                    selected_sub = option_menu(
                        menu_title="Submenu",
                        options=[sub['title'] for sub in menu['submenu']],
                        icons=[sub['icon'] for sub in menu['submenu']],
                        menu_icon="bi-tools",
                        default_index=0
                    )
                execute_menu_action(selected_sub, menu['submenu'])
            else:
                execute_menu_action(menu['title'], menus['menus'])

def execute_menu_action(selected, items):
    for item in items:
        if selected == item['title']:
            # Dynamically call the function from the my_pages module
            module = globals().get(item['module'])
            if module and hasattr(module, 'show'):
                module.show()

if __name__ == '__main__':
    main()
