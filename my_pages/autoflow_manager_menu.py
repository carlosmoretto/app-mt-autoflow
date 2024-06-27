import streamlit as st
import json
import os

def load_menu_config():
    config_path = 'config/menus.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_menu_config(config):
    config_path = 'config/menus.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def show():
    st.title("Gerenciador de Menus")
    menus = load_menu_config()

    # Adicionar um novo menu principal
    with st.form("add_menu"):
        st.write("## Adicionar Novo Menu Principal")
        new_menu_title = st.text_input("Título do Menu", "")
        new_menu_icon = st.text_input("Ícone do Menu", "")
        new_menu_module = st.text_input("Módulo do Menu", "")
        if st.form_submit_button("Adicionar Menu"):
            if new_menu_title:
                menus['menus'].append({"title": new_menu_title, "icon": new_menu_icon, "module": new_menu_module, "permissions": ["User", "Admin"]})
                save_menu_config(menus)
                st.experimental_rerun()

    # Exibir menus existentes
    for i, menu in enumerate(menus['menus']):
        with st.expander(f"{menu['title']} (clique para expandir/recolher)"):
            with st.form(f"edit_menu_{i}"):
                st.text_input("Título", value=menu['title'], key=f"title_{i}")
                st.text_input("Ícone", value=menu['icon'], key=f"icon_{i}")
                st.text_input("Módulo", value=menu.get('module', ''), key=f"module_{i}")
                st.number_input("Ordem", value=menu['order'], key=f"order_{i}")
                if st.form_submit_button("Salvar Alterações"):
                    menu['title'] = st.session_state[f"title_{i}"]
                    menu['icon'] = st.session_state[f"icon_{i}"]
                    menu['module'] = st.session_state[f"module_{i}"]
                    menu['order'] = st.session_state[f"order_{i}"]
                    save_menu_config(menus)
                    st.experimental_rerun()
                if st.form_submit_button("Excluir Menu"):
                    del menus['menus'][i]
                    save_menu_config(menus)
                    st.experimental_rerun()

            # Selecionar e editar submenus
            if 'submenu' in menu:
                submenu_titles = [submenu['title'] for submenu in menu['submenu']]
                selected_submenu = st.selectbox("Escolha um submenu para editar", options=submenu_titles, key=f"submenu_{i}")
                selected_index = submenu_titles.index(selected_submenu)
                submenu = menu['submenu'][selected_index]
                with st.form(f"edit_submenu_{i}_{selected_index}"):
                    st.text_input("Título do Submenu", value=submenu['title'], key=f"sub_title_{i}_{selected_index}")
                    st.text_input("Ícone do Submenu", value=submenu['icon'], key=f"sub_icon_{i}_{selected_index}")
                    st.text_input("Módulo do Submenu", value=submenu.get('module', ''), key=f"sub_module_{i}_{selected_index}")
                    st.number_input("Ordem do Submenu", value=submenu['order'], key=f"sub_order_{i}_{selected_index}")
                    if st.form_submit_button("Salvar Submenu"):
                        submenu['title'] = st.session_state[f"sub_title_{i}_{selected_index}"]
                        submenu['icon'] = st.session_state[f"sub_icon_{i}_{selected_index}"]
                        submenu['module'] = st.session_state[f"sub_module_{i}_{selected_index}"]
                        submenu['order'] = st.session_state[f"sub_order_{i}_{selected_index}"]
                        save_menu_config(menus)
                        st.experimental_rerun()
                    if st.form_submit_button("Excluir Submenu"):
                        del menu['submenu'][selected_index]
                        save_menu_config(menus)
                        st.experimental_rerun()

    # Adicionar um novo submenu no menu selecionado
    with st.form("add_submenu"):
        st.write("### Adicionar Novo Submenu ao Menu Selecionado")
        menu_titles = [menu['title'] for menu in menus['menus']]
        selected_menu = st.selectbox("Escolha um menu para adicionar um submenu", options=menu_titles, key="selected_menu")
        selected_menu_index = menu_titles.index(selected_menu)
        new_sub_title = st.text_input("Título do Submenu", key="new_sub_title")
        new_sub_icon = st.text_input("Ícone do Submenu", key="new_sub_icon")
        new_sub_module = st.text_input("Módulo do Submenu", key="new_sub_module")
        if st.form_submit_button("Adicionar Submenu"):
            if 'submenu' not in menus['menus'][selected_menu_index]:
                menus['menus'][selected_menu_index]['submenu'] = []
            menus['menus'][selected_menu_index]['submenu'].append({"title": new_sub_title, "icon": new_sub_icon, "module": new_sub_module, "permissions": ["User", "Admin"]})
            save_menu_config(menus)
            st.experimental_rerun()

if __name__ == '__main__':
    show()
