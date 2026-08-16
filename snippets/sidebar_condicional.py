# Sidebar condicional reutilizável
import streamlit as st

def render_sidebar():
    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False

    if st.session_state["is_admin"]:
        st.sidebar.title("Admin")
        st.sidebar.button("Dashboard")
        st.sidebar.button("Faturamento")
        st.sidebar.button("Clientes")
        st.sidebar.button("Estoque")
        if st.sidebar.button("Sair"):
            st.session_state["is_admin"] = False
            st.experimental_rerun()
    else:
        st.sidebar.title("Loja")
        st.sidebar.button("Início")
        st.sidebar.button("Catálogo")
        st.sidebar.button("Ideias")
        st.sidebar.button("Carrinho")
