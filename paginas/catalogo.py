import base64
from io import BytesIO
import streamlit as st
from PIL import Image, ImageOps


def ajustar_imagem_quadrada(img_input, tamanho=(160, 160)):
    if not img_input:
        return None
    try:
        if isinstance(img_input, str):
            if "," in img_input:
                img_input = img_input.split(",")[1]
            image_bytes = base64.b64decode(img_input)
            img = Image.open(BytesIO(image_bytes))
        else:
            img = Image.open(img_input)
        img = img.convert("RGB")
        img_fit = ImageOps.fit(
            img, tamanho,
            Image.Resampling.LANCZOS,
            centering=(0.5, 0.5)
        )
        return img_fit
    except Exception as e:
        print(f"Erro ao ajustar imagem: {e}")
        return None


def render_catalogo(conn, cursor, converter_imagem_base64=None):
    st.title("🧩 Catálogo de Peças")

    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []
    if "quantidades" not in st.session_state:
        st.session_state.quantidades = {}

    st.markdown("""
    <style>
    .peca-imagem {
        width: 160px;
        height: 160px;
        margin: 0 auto 0.8rem auto;
        border-radius: 8px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #262730;
    }
    .peca-nome {
        font-size: 0.95rem;
        line-height: 1.2;
        min-height: 2.4rem;
        display: flex;
        align-items: center;
        margin: 0 0 0.6rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    qtd_no_carrinho = len(st.session_state.carrinho)
    if st.button(
        f"🛒 Ir para o Carrinho ({qtd_no_carrinho} {'item' if qtd_no_carrinho == 1 else 'itens'})",
        use_container_width=True,
        type="primary",
        key="btn_ir_carrinho"
    ):
        st.session_state.pagina_atual = "Carrinho"  # ✅ NOME CORRETO!
        st.rerun()

    st.divider()

    cursor.execute("""
        SELECT p.id, p.nome_peca, p.tempo_h, p.preco_sugerido, p.imagem, p.peso_g, p.material_id
        FROM pecas_padrao p
    """)
    pecas = cursor.fetchall()

    if not pecas:
        st.info("Nenhuma peça disponível no catálogo no momento.")
        return

    cols_per_row = 4

    for i in range(0, len(pecas), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(pecas):
                idx = i + j
                p_id, p_nome, p_tempo, p_preco, p_imagem, p_peso, p_material_id = pecas[idx]
                chave_qtd = f"qtd_{p_id}"

                if chave_qtd not in st.session_state.quantidades:
                    st.session_state.quantidades[chave_qtd] = 1

                with cols[j]:
                    with st.container(border=True):
                        st.markdown(f"<h3 class='peca-nome'>📦 {p_nome}</h3>", unsafe_allow_html=True)

                        if p_imagem:
                            img_redimensionada = ajustar_imagem_quadrada(p_imagem)
                            if img_redimensionada:
                                st.image(img_redimensionada, width=160)
                        else:
                            st.markdown("""
                                <div class='peca-imagem' style='color:#808495;'>🖼️ Sem foto</div>
                            """, unsafe_allow_html=True)

                        st.write(f"⏱️ **Tempo:** {p_tempo}h")
                        st.write(f"💰 **Preço:** R$ {p_preco:.2f}")

                        c1, c2, c3 = st.columns([1, 1.2, 1])
                        with c1:
                            if st.button("➖", key=f"menos_{p_id}") and st.session_state.quantidades[chave_qtd] > 1:
                                st.session_state.quantidades[chave_qtd] -= 1
                        with c2:
                            st.markdown(f"<h3 style='text-align:center; margin:0;'>{st.session_state.quantidades[chave_qtd]}</h3>", unsafe_allow_html=True)
                        with c3:
                            if st.button("➕", key=f"mais_{p_id}"):
                                st.session_state.quantidades[chave_qtd] += 1

                        if st.button("🛒 Adicionar", key=f"add_{p_id}", use_container_width=True):
                            qtd = st.session_state.quantidades[chave_qtd]
                            st.session_state.carrinho.append({
                                "nome": p_nome if qtd == 1 else f"{p_nome} (x{qtd})",
                                "peso": (float(p_peso) if p_peso else 0.0) * qtd,
                                "tempo": (float(p_tempo) if p_tempo else 0.0) * qtd,
                                "valor": float(p_preco) * qtd,
                                "material_nome": "",
                                "material_id": p_material_id,
                                "imagem": p_imagem,
                            })
                            st.session_state.quantidades[chave_qtd] = 1
                            st.toast(f"{qtd}x {p_nome} adicionado!", icon="🛒")
                            st.rerun()
