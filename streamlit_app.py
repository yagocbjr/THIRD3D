import streamlit as st
import runpy
import os
from snippets.sidebar_condicional import render_sidebar

st.set_page_config(page_title="THIRD3D", layout="wide")
render_sidebar()

# Mapa de páginas: rótulo -> caminho relativo do arquivo
PAGES = {
    "Início": "paginas/cliente/inicio.py",
    "Catálogo": "paginas/cliente/catalogo.py",
    "Carrinho": "paginas/cliente/carrinho.py",
    "Ideias": "paginas/cliente/ideias.py",
    "Admin - Dashboard": "paginas/admin/dashboard.py",
    "Admin - Faturamento": "paginas/admin/faturamento.py",
    "Admin - Estoque": "paginas/admin/estoque.py",
}

# Menu principal na sidebar
page = st.sidebar.selectbox("Navegar", list(PAGES.keys()))

# Executa o arquivo selecionado (cada arquivo está escrito para rodar sozinho)
page_path = PAGES[page]
if os.path.exists(page_path):
    runpy.run_path(page_path, run_name="__main__")
else:
    st.error(f"Arquivo não encontrado: {page_path}")
