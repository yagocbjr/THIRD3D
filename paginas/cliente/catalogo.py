import streamlit as st

st.set_page_config(page_title="Catálogo - Loja 3D")

# Dados de exemplo
PRODUTOS = [
    {"id":1, "nome":"Suporte para Fone", "categoria":"Acessórios", "preco":45.0, "badge":"novo"},
    {"id":2, "nome":"Vaso Minimalista", "categoria":"Decoração", "preco":60.0, "badge":""},
    {"id":3, "nome":"Peça Engrenagem", "categoria":"Peças Técnicas", "preco":30.0, "badge":"mais vendido"},
    {"id":4, "nome":"Organizador de Cabos", "categoria":"Acessórios", "preco":25.0, "badge":""},
]

if "cart" not in st.session_state:
    st.session_state["cart"] = []

st.title("Catálogo")

# Filtros
categorias = ["Todas"] + sorted(list({p["categoria"] for p in PRODUTOS}))
sel_cat = st.selectbox("Categoria", categorias)
q = st.text_input("Pesquisar por nome")

filt = []
for p in PRODUTOS:
    if sel_cat != "Todas" and p["categoria"] != sel_cat:
        continue
    if q and q.lower() not in p["nome"].lower():
        continue
    filt.append(p)

cols = st.columns(2)
for i, p in enumerate(filt):
    c = cols[i % 2]
    with c:
        st.image("https://via.placeholder.com/300.png?text=" + p["nome"].replace(" ", "+"))
        badge = f"<div class='badge'>{p['badge']}</div>" if p['badge'] else ""
        st.markdown(f"<div class='card'>{badge}<h3>{p['nome']}</h3><p>R$ {p['preco']:.2f}</p></div>", unsafe_allow_html=True)
        if st.button("Adicionar ao carrinho - %s" % p["id"]):
            st.session_state["cart"].append(p)
            st.success(f"{p['nome']} adicionado ao carrinho")

