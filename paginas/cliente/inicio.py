import streamlit as st

st.set_page_config(page_title="Início - Loja 3D", layout="wide")

# Carrega CSS
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("THIRD3D — Impressão 3D")
st.subheader("Peças sob medida e produção local")

col1, col2 = st.columns([2,1])
with col1:
    st.image("https://via.placeholder.com/900x300.png?text=Hero+THIRD3D", use_column_width=True)
    st.markdown("#### Quem somos\nProduzimos peças em 3D com atenção aos detalhes. Prazo médio de entrega: 3–7 dias úteis.")

with col2:
    st.markdown("""
    <div style="display:flex; flex-direction:column; gap:8px;">
      <a href="https://wa.me/5511904460488" target="_blank" class="btn btn-whatsapp">💬 Fale no WhatsApp</a>
      <a href="https://instagram.com/SEU_USUARIO" target="_blank" class="btn btn-instagram">📸 Instagram</a>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

st.header("Peças em destaque")
cols = st.columns(4)
for i, c in enumerate(cols):
    with c:
        st.image("https://via.placeholder.com/300.png?text=Produto+%d" % (i+1))
        st.markdown(f"**Produto {i+1}**\n\nR$ 45,00")

st.markdown("\n\n")
st.info("Use o menu para navegar: Catálogo / Ideias / Carrinho")
