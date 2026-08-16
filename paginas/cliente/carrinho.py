import streamlit as st
import urllib.parse

st.title("Carrinho")

if "cart" not in st.session_state:
    st.session_state["cart"] = []

cart = st.session_state["cart"]

if not cart:
    st.info("Seu carrinho está vazio")
else:
    total = sum(item['preco'] for item in cart)
    for idx, item in enumerate(cart):
        st.write(f"{idx+1}. {item['nome']} — R$ {item['preco']:.2f}")
        if st.button(f"Remover {idx}"):
            cart.pop(idx)
            st.experimental_rerun()

    st.sidebar.header("Resumo do Pedido")
    st.sidebar.write(f"{len(cart)} itens")
    st.sidebar.write(f"Subtotal: R$ {total:.2f}")

    # Finalizar via WhatsApp
    resumo = "\n".join([f"- {i['nome']} (R$ {i['preco']:.2f})" for i in cart])
    mensagem = f"Olá! Gostaria de fazer o pedido:\n{resumo}\nTotal: R$ {total:.2f}"
    link = f"https://wa.me/5511904460488?text={urllib.parse.quote(mensagem)}"
    st.markdown(f'<a href="{link}" target="_blank">Finalizar pedido no WhatsApp</a>', unsafe_allow_html=True)

