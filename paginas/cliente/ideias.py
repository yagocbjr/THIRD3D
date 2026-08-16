import streamlit as st

st.title("Ideias Personalizadas")

with st.form("ideia_form"):
    nome = st.text_input("Seu nome")
    contato = st.text_input("Telefone ou e-mail")
    descricao = st.text_area("Descreva a peça ou ideia")
    prazo = st.selectbox("Prazo desejado", ["Urgente (1-2 dias)", "3-7 dias", "+7 dias"])
    enviar = st.form_submit_button("Enviar pedido de ideia")

if enviar:
    # salvar localmente na sessão (exemplo). Em produção, salvar em DB ou enviar por e-mail
    if "ideias" not in st.session_state:
        st.session_state["ideias"] = []
    st.session_state["ideias"].append({"nome":nome, "contato":contato, "descricao":descricao, "prazo":prazo})
    st.success("Pedido enviado! Entraremos em contato em breve.")

