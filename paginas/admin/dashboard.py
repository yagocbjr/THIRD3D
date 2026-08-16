import streamlit as st

# Página admin — dashboard (temporário)

# Inicializa estado
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False

# Login temporário: admin / 123
if not st.session_state["is_admin"]:
    st.title("Login Admin (temporário)")
    user = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "admin" and pwd == "123":
            st.session_state["is_admin"] = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")
    st.stop()

# Conteúdo do dashboard
st.title("Painel Admin")
st.metric("Vendas hoje", "12", delta="+3")
st.metric("Pedidos em fila", "4")

st.markdown("---")
st.header("Visão geral")
st.write("Gráficos e KPIs vão aqui. (Exemplo)")

if st.button("Sair da Área Admin"):
    st.session_state["is_admin"] = False
    st.experimental_rerun()
