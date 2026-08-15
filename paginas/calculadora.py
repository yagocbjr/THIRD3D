import streamlit as st


def render_calculadora(conn, cursor):
    """Área administrativa: calcula peças avulsas e adiciona ao carrinho.
    O checkout fica na página Carrinho pública."""
    st.title("🧮 Calculadora de Peças (Admin)")
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []
    cursor.execute("""
        SELECT m.id, mc.nome, m.cor, m.tipo, m.preco_kg, m.nome
        FROM materiais m
        LEFT JOIN marcas mc ON m.marca_id = mc.id
    """)
    materiais_cadastrados = cursor.fetchall()
    if not materiais_cadastrados:
        st.warning("⚠️ Cadastre materiais no estoque antes de realizar orçamentos!")
        return
    st.subheader("Calcular Peça Avulsa")
    dict_mats = {
        f"{m[1] or ''} - {m[2] or ''} ({m[3] or ''}) (R$ {m[4]:.2f}/Kg)": m
        for m in materiais_cadastrados
    }
    mat_escolhido = st.selectbox("Filamento:", list(dict_mats.keys()), key="calc_material")
    mat_dados = dict_mats[mat_escolhido]
    v_item_mat_id = mat_dados[0]
    preco_filamento_kg = float(mat_dados[4])
    v_item_nome = st.text_input("Nome da Peça Avulsa", value="", key="calc_nome_peca")
    c_a, c_b = st.columns(2)
    with c_a:
        peso_g = st.number_input(
            "Peso (g)", min_value=0.1, value=50.0, step=10.0, key="calc_peso"
        )
        st.write("Tempo de Impressão")
        c_h, c_m = st.columns(2)
        with c_h:
            horas_parte = st.number_input(
                "Horas", min_value=0, value=2, step=1, key="calc_tempo_horas"
            )
        with c_m:
            minutos_parte = st.number_input(
                "Minutos", min_value=0, max_value=59, value=0, step=1, key="calc_tempo_minutos"
            )
        horas_impressao = horas_parte + (minutos_parte / 60.0)
        st.caption(f"⏱️ Total: {horas_parte}h {minutos_parte}min ({horas_impressao:.2f}h decimais)")
    with c_b:
        custo_hora_maquina = st.number_input(
            "Custo Hora (R$)", min_value=0.0, value=2.50, step=0.50, key="calc_custo_hora"
        )
        margem_lucro = st.number_input(
            "Margem (%)", min_value=0.0, value=100.0, step=10.0, key="calc_margem"
        )
    v_c_mat = (peso_g / 1000.0) * preco_filamento_kg
    v_c_maq = horas_impressao * custo_hora_maquina
    v_calc = (v_c_mat + v_c_maq) * (1.0 + (margem_lucro / 100.0))

    res1, res2 = st.columns(2)
    res1.write(f"📊 **Custo de Produção:** R$ {(v_c_mat + v_c_maq):.2f}")
    res2.write(f"💰 **Preço de Venda Sugerido:** R$ {v_calc:.2f}")

    preco_avulso_negociado = st.number_input(
        "Preço Final Ajustado (R$)*",
        min_value=0.0,
        value=float(v_calc),
        step=1.0,
        key="calc_preco_final"
    )
    # ✅ Botão com CHAVE obrigatória
    if st.button("➕ Adicionar Peça Avulsa ao Carrinho", type="primary", key="calc_btn_adicionar"):
        if v_item_nome.strip():
            nome_mat_limpo = f"{mat_dados[1] or ''} {mat_dados[2] or ''}".strip()
            st.session_state.carrinho.append({
                "nome": v_item_nome.strip(),
                "peso": peso_g,
                "tempo": horas_impressao,
                "valor": preco_avulso_negociado,
                "material_nome": nome_mat_limpo,
                "material_id": v_item_mat_id,
                "imagem": None,
            })
            st.toast(f"'{v_item_nome}' adicionado ao carrinho!", icon="🛒")
            st.rerun()
        else:
            st.error("Digite o nome da peça avulsa.")
    st.divider()
    # ✅ Botão para ir direto pro Carrinho
    qtd = len(st.session_state.carrinho)
    st.caption(f"🛒 Itens no carrinho: {qtd}")
    if st.button("🛒 Ir para o Carrinho Finalizar", use_container_width=True, key="calc_btn_ir_carrinho"):
        st.session_state.pagina_atual = "Carrinho"
        st.rerun()
