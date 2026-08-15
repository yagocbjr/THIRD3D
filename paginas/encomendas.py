import base64
import io
import streamlit as st
from PIL import Image


def _converter_imagem_ideia(uploaded_file, largura_max=300, qualidade=80):
    """Converte a foto opcional de referência em base64, mesmo padrão usado no catálogo."""
    if uploaded_file is None:
        return None
    try:
        img = Image.open(uploaded_file)
        img = img.convert("RGB")
        w, h = img.size
        if w > largura_max:
            proporcao = largura_max / w
            nova_largura = largura_max
            nova_altura = int(h * proporcao)
            img = img.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=qualidade, optimize=True)
        base64_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/jpeg;base64,{base64_str}"
    except Exception:
        return None


def render_encomendas(conn, cursor):
    """Formulário PÚBLICO — o cliente só registra o pedido de ideia.
    A definição de status/prioridade e a visão de todas as ideias fica
    exclusivamente na página Quadro de Ideias (admin)."""
    st.title("💡 Ideias Personalizadas")
    st.caption("Conte pra gente o que você precisa — a gente cuida do resto!")

    with st.form("form_nova_ideia", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            cli_nome = st.text_input("Seu Nome*", placeholder="Ex: João da Silva")
            cli_telefone = st.text_input("Telefone / WhatsApp (Opcional)", placeholder="(XX) XXXXX-XXXX")
            descricao = st.text_input("O que você quer?*", placeholder="Ex: Boneco Homem de Ferro 15cm, Peça do Gol 94...")
            prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "🚨 Urgente"])

        with col2:
            ref_link = st.text_input("Link de Referência (Opcional)", placeholder="https://makerworld.com/...")
            foto_upload = st.file_uploader("📷 Ou carregue uma foto de referência (Opcional)", type=["png", "jpg", "jpeg"])
            obs = st.text_area("Observações / Detalhes", placeholder="Ex: Quer na cor preta, aniversário dia 20...")

        enviado = st.form_submit_button("💾 Enviar Ideia", use_container_width=True, type="primary")

        if enviado:
            if not cli_nome.strip() or not descricao.strip():
                st.error("Preencha pelo menos seu nome e a descrição do pedido!")
            else:
                imagem_b64 = _converter_imagem_ideia(foto_upload)
                cursor.execute("""
                    INSERT INTO ideias_personalizadas (cliente_nome, telefone, descricao, referencia_link, imagem, prioridade, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (cli_nome.strip(), cli_telefone.strip(), descricao.strip(), ref_link.strip(), imagem_b64, prioridade, obs.strip()))
                conn.commit()
                st.success("✅ Ideia enviada! Vamos avaliar e entrar em contato em breve.")
