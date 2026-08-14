import base64
from io import BytesIO
import streamlit as st
from PIL import Image, ImageOps

# ✅ CSS AJUSTADO PARA 4 COLUNAS + EXPANDER SEM BATER NAS BORDAS
st.markdown("""
<style>
/* Container da imagem — quadrado e centralizada */
div[data-testid="stImage"] {
    width: 160px !important;
    height: 160px !important;
    margin: 0 auto 0.8rem auto !important;
    padding: 0 !important;
}
.stImage > img {
    width: 160px !important;
    height: 160px !important;
    object-fit: cover !important;
    object-position: center !important;
    border-radius: 8px !important;
}
/* Card — espaçamento equilibrado */
div[data-testid="stContainer"] {
    padding: 1rem !important;
}
/* ✅ NOME — FONTE MENOR E ALTURA FIXA */
div[data-testid="stContainer"] h3 {
    font-size: 0.95rem !important;  /* Menor */
    line-height: 1.2 !important;
    min-height: 2.4rem !important; /* ✅ Altura igual para TODOS os nomes */
    display: flex !important;
    align-items: center !important;
    margin: 0 0 0.6rem 0 !important;
}
/* ✅ EXPANDER — LARGURA REDUZIDA COM MARGEM */
div[data-testid="stExpander"] {
    width: 90% !important;
    margin: 0 auto !important;
}
div[data-testid="stExpander"] details {
    padding: 0.5rem !important;
}
div[data-testid="stExpander"] div[class*="content"] {
    padding: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

def ajustar_imagem_quadrada(img_input, tamanho=(160, 160)):
    """✅ CORTA DO CENTRO — TAMANHO AJUSTADO PARA 4 COLUNAS"""
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


def render_catalogo(conn, cursor, converter_imagem_base64):
    st.title("🧩 Catálogo de Peças Padrão")

    # 1. Busca materiais no estoque
    cursor.execute("""
        SELECT m.id, mc.nome, m.cor, m.tipo, m.preco_kg, m.nome
        FROM materiais m
        LEFT JOIN marcas mc ON m.marca_id = mc.id
    """)
    materiais_cadastrados = cursor.fetchall()

    if not materiais_cadastrados:
        st.warning(
            "⚠️ Cadastre materiais no estoque antes de registrar peças padrão!"
        )
    else:
        # --- FORMULÁRIO DE CADASTRO ---
        with st.expander("➕ Cadastrar Nova Peça Padrão", expanded=True):
            dict_mats = {
                f"{m[1] or ''} - {m[2] or ''} ({m[3] or ''}) (R$ {m[4]:.2f}/Kg)": m
                for m in materiais_cadastrados
            }
            mat_escolhido = st.selectbox(
                "Filamento Usado na Peça:",
                list(dict_mats.keys()),
                key="cat_mat",
            )

            mat_dados = dict_mats[mat_escolhido]
            mat_id = mat_dados[0]
            preco_filamento_kg = float(mat_dados[4])

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                nome_peca_padrao = st.text_input(
                    "Nome da Peça Padrão (ex: Suporte de Celular)"
                )
                peso_padrao = st.number_input(
                    "Peso (gramas)",
                    min_value=0.1,
                    value=80.0,
                    step=10.0,
                    key="cat_peso",
                )
                foto_upload = st.file_uploader(
                    "📷 Foto da Peça (PNG/JPG)",
                    type=["png", "jpg", "jpeg"],
                    key="cat_foto",
                )
                custo_adicional = st.number_input(
                    "📦 Custos Extras / Insumos (R$) (Chaveiro, Caixa, Switch, etc)",
                    min_value=0.0,
                    value=0.0,
                    step=0.50,
                    key="cat_custo_add",
                )

            with col_c2:
                tempo_padrao = st.number_input(
                    "Tempo de Impressão (Horas)",
                    min_value=0.0,
                    value=3.0,
                    step=0.5,
                    key="cat_tempo",
                )
                custo_h_padrao = st.number_input(
                    "Custo Hora/Máquina (R$)",
                    min_value=0.0,
                    value=2.50,
                    step=0.50,
                    key="cat_custo_h",
                )
                margem_padrao = st.number_input(
                    "Margem de Lucro (%)",
                    min_value=0.0,
                    value=100.0,
                    step=10.0,
                    key="cat_lucro",
                )

            # CÁLCULO INCLUINDO CUSTOS EXTRAS
            c_mat = (peso_padrao / 1000.0) * preco_filamento_kg
            c_maq = tempo_padrao * custo_h_padrao
            custo_producao_calc = c_mat + c_maq + custo_adicional
            preco_final_padrao = custo_producao_calc * (
                1.0 + (margem_padrao / 100.0)
            )

            res1, res2 = st.columns(2)
            res1.write(
                f"📊 **Custo de Produção:** R$ {custo_producao_calc:.2f}"
            )
            res2.write(
                f"💰 **Preço Sugerido de Venda:** R$ {preco_final_padrao:.2f}"
            )

            if st.button("💾 Salvar Peça no Catálogo", type="primary"):
                if nome_peca_padrao.strip():
                    imagem_b64 = converter_imagem_base64(foto_upload)

                    try:
                        cursor.execute(
                            """
                            INSERT INTO pecas_padrao (nome_peca, material_id, peso_g, tempo_h, preco_sugerido, custo_producao, imagem, custo_adicional)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                nome_peca_padrao.strip(),
                                mat_id,
                                peso_padrao,
                                tempo_padrao,
                                preco_final_padrao,
                                custo_producao_calc,
                                imagem_b64,
                                custo_adicional,
                            ),
                        )
                    except Exception:
                        cursor.execute(
                            """
                            INSERT INTO pecas_padrao (nome_peca, material_id, peso_g, tempo_h, preco_sugerido, custo_producao, imagem)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                nome_peca_padrao.strip(),
                                mat_id,
                                peso_padrao,
                                tempo_padrao,
                                preco_final_padrao,
                                custo_producao_calc,
                                imagem_b64,
                            ),
                        )

                    conn.commit()
                    st.success(f"Peça '{nome_peca_padrao}' salva no catálogo!")
                    st.rerun()
                else:
                    st.error("Por favor, digite o nome da peça.")

        # --- LISTAGEM DAS PEÇAS — ✅ 4 POR LINHA! ---
        st.divider()
        st.subheader("Peças Cadastradas no Catálogo")

        cursor.execute("""
            SELECT p.id, p.nome_peca, mc.nome, m.cor, m.tipo, p.peso_g, p.tempo_h, p.preco_sugerido, p.custo_producao, p.imagem
            FROM pecas_padrao p
            LEFT JOIN materiais m ON p.material_id = m.id
            LEFT JOIN marcas mc ON m.marca_id = mc.id
        """)
        pecas = cursor.fetchall()

        if pecas:
            # ✅ MUDOU AQUI: 4 colunas por linha!
            cols_per_row = 4

            for i in range(0, len(pecas), cols_per_row):
                cols = st.columns(cols_per_row)

                for j in range(cols_per_row):
                    if i + j < len(pecas):
                        idx = i + j
                        p = pecas[idx]
                        (
                            p_id,
                            p_nome,
                            mc_nome,
                            m_cor,
                            m_tipo,
                            p_peso,
                            p_tempo,
                            p_preco,
                            p_custo,
                            p_imagem,
                        ) = p

                        with cols[j]:
                            with st.container(border=True):
                                # ✅ Nome centralizado
                                st.markdown(f"### 📦 {p_nome}")

                                # ✅ Imagem quadrada 160x160 centralizada
                                if p_imagem:
                                    img_redimensionada = ajustar_imagem_quadrada(p_imagem)
                                    if img_redimensionada:
                                        st.image(img_redimensionada, width=160, use_container_width=False)
                                else:
                                    st.markdown(
                                        """
                                        <div style="height:160px; width:160px; margin:0 auto; background-color:#262730; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#808495;">
                                            🖼️ Sem foto
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                # ✅ Detalhes com espaço interno
                                with st.expander("🔍 Ver Detalhes"):
                                    mat_str = f"{mc_nome or ''} - {m_cor or ''} ({m_tipo or ''})"
                                    st.caption(f"**Material:** {mat_str}")
                                    st.caption(f"⚖️ **{p_peso}g** | ⏱️ **{p_tempo}h**")
                                    st.write(f"🏭 Custo: **R$ {p_custo:.2f}**")
                                    st.write(f"💰 Preço: **R$ {p_preco:.2f}**")

                                    if st.button(
                                        "❌ Excluir",
                                        key=f"del_peca_{p_id}_{idx}",
                                        use_container_width=True,
                                    ):
                                        cursor.execute(
                                            "DELETE FROM pecas_padrao WHERE id = ?",
                                            (p_id,),
                                        )
                                        conn.commit()
                                        st.rerun()
        else:
            st.info("Nenhuma peça cadastrada no catálogo ainda.")