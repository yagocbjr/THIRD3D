import streamlit as st
# admin — faturamento (temporário)
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if not st.session_state["is_admin"]:
    st.title("Área Administrativa — Login")
    user = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if user == "admin" and pwd == "123":
            st.session_state["is_admin"] = True
            st.experimental_rerun()
        else:
            st.error("Usuário ou senha inválidos")
    st.stop()

st.title("Faturamento")
st.write("Tabela de faturas (placeholder)")

if st.button("Sair da Área Admin"):
    st.session_state["is_admin"] = False
    st.experimental_rerun()
