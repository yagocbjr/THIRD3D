import streamlit as st

# ✅ CSS — RECOLHÍVEIS + ABAS LADO A LADO
st.markdown("""
<style>
/* ========== BOTÕES FILTRO — LADO A LADO ========== */
div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"][data-testid*="filtro_"]) {
    gap: 10px !important;
    flex-wrap: wrap !important;
    margin-bottom: 1.2rem !important;
}
div.stButton > button[kind="secondary"][data-testid*="filtro_"] {
    border-radius: 10px !important;
    padding: 8px 18px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    margin: 0 !important;
    height: auto !important;
    min-height: 40px !important;
}
div.stButton > button[kind="secondary"][data-testid*="filtro_Pendente"] {
    background: rgba(96, 165, 250, 0.22) !important;
    color: #93c5fd !important;
    border-color: rgba(96, 165, 250, 0.35) !important;
}
div.stButton > button[kind="secondary"][data-testid*="filtro_Imprimindo"] {
    background: rgba(251, 191, 36, 0.22) !important;
    color: #fcd34d !important;
    border-color: rgba(251, 191, 36, 0.35) !important;
}
div.stButton > button[kind="secondary"][data-testid*="filtro_Concluído"] {
    background: rgba(74, 222, 128, 0.22) !important;
    color: #86efac !important;
    border-color: rgba(74, 222, 128, 0.35) !important;
}
div.stButton > button[kind="secondary"][data-testid*="filtro_Cancelado"] {
    background: rgba(248, 113, 113, 0.22) !important;
    color: #fca5a5 !important;
    border-color: rgba(248, 113, 113, 0.35) !important;
}

/* ========== EXPANDER RECOLHÍVEL — ESTILO VIDRO ========== */
div[data-testid="stExpander"] {
    background: rgba(35, 35, 45, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(12px) !important;
    margin-bottom: 0.5rem !important;
}
/* Título do resumo — o que fica visível recolhido */
div[data-testid="stExpander"] summary p {
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    margin: 0 !important;
}
/* Conteúdo aberto — detalhes */
div[data-testid="stExpander"] .streamlit-expanderContent {
    padding: 0.8rem 1rem !important;
    font-size: 0.85rem !important;
}

/* ========== BOTÕES DE STATUS INTERNOS ========== */
div.stButton > button[data-testid*="status_"] {
    border-radius: 7px !important;
    padding: 4px 8px !important;
    font-size: 0.75rem !important;
    min-width: 70px !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    margin: 2px !important;
}
div.stButton > button[kind="secondary"][data-testid*="Pendente"] {
    background: rgba(96, 165, 250, 0.18) !important;
    color: #93c5fd !important;
}
div.stButton > button[kind="secondary"][data-testid*="Imprimindo"] {
    background: rgba(251, 191, 36, 0.18) !important;
    color: #fcd34d !important;
}
div.stButton > button[kind="secondary"][data-testid*="Concluído"] {
    background: rgba(74, 222, 128, 0.18) !important;
    color: #86efac !important;
}
div.stButton > button[kind="secondary"][data-testid*="Cancelado"] {
    background: rgba(248, 113, 113, 0.18) !important;
    color: #fca5a5 !important;
}
</style>
""", unsafe_allow_html=True)


def render_pedidos(conn, cursor, formatar_nome_material):
    st.title("📋 Fila de Impressão e Pedidos")

    STATUS_OPCOES = [
        ("Pendente", "⏳"),
        ("Imprimindo", "🖨️"),
        ("Concluído", "✅"),
        ("Cancelado", "❌"),
    ]
    status_icones = {s[0]: s[1] for s in STATUS_OPCOES}

    # FILTRO — BOTÕES LADO A LADO
    if "filtro_status" not in st.session_state:
        st.session_state.filtro_status = "Pendente"

    cols_filtro = st.columns(len(STATUS_OPCOES))
    for col, (status_nome, icone) in zip(cols_filtro, STATUS_OPCOES):
        with col:
            if st.button(f"{icone} {status_nome}", key=f"filtro_{status_nome}", type="secondary"):
                st.session_state.filtro_status = status_nome
                st.rerun()

    status_filtro = st.session_state.filtro_status

    # BUSCA PEDIDOS
    cursor.execute("""
        SELECT p.id, p.cliente, p.nome_peca, mc.nome, m.cor, m.tipo, p.peso_g, p.tempo_h, p.valor_total, p.status, p.material_id, p.estoque_baixado, m.nome, p.data_criado
        FROM pedidos p
        LEFT JOIN materiais m ON p.material_id = m.id
        LEFT JOIN marcas mc ON m.marca_id = mc.id
        WHERE p.status = ?
        ORDER BY p.id DESC
    """, (status_filtro,))
    pedidos_filtrados = cursor.fetchall()

    # ✅ 2 POR LINHA + RECOLHÍVEIS (só resumo visível)
    if pedidos_filtrados:
        for i in range(0, len(pedidos_filtrados), 2):
            par = pedidos_filtrados[i:i+2]
            colunas = st.columns(2)

            for col, ped in zip(colunas, par):
                ped_id, cli, peca, mc_nome, m_cor, m_tipo, peso, tempo, valor, status, mat_id, baixado, m_nome_antigo, data_criado = ped
                mat_str = formatar_nome_material(mat_id, mc_nome, m_cor, m_tipo, m_nome_antigo)
                icone_atual = status_icones.get(status, "🔄")
                data_fmt = data_criado[:10] if data_criado else "Sem data"

                with col:
                    # ✅ RECOLHÍVEL: FECHADO POR PADRÃO → SÓ MOSTRA NÚMERO + CLIENTE
                    with st.expander(f"{icone_atual} Pedido #{ped_id} — {cli}", expanded=False):
                        # DETALHES — SÓ APARECEM AO CLICAR
                        st.markdown(f"""
                        <p><strong>📅 Data:</strong> {data_fmt} &nbsp;|&nbsp; <strong>📦 Peça:</strong> {peca}</p>
                        <p><strong>🧵 Material:</strong> {mat_str}</p>
                        <p>⚖️ {peso:.1f}g &nbsp;|&nbsp; ⏱️ {tempo:.1f}h &nbsp;|&nbsp; 💰 R$ {valor:.2f}</p>
                        """, unsafe_allow_html=True)

                        # VALOR + BOTÕES DE STATUS
                        col_val, col_btns = st.columns([1, 2])
                        with col_val:
                            novo_valor = st.number_input(
                                f"Valor #{ped_id}", min_value=0.0,
                                value=float(valor), step=1.0,
                                key=f"val_{ped_id}_{status_filtro}",
                                label_visibility="collapsed"
                            )
                            if novo_valor != valor:
                                if st.button("💾 Salvar", key=f"btn_val_{ped_id}_{status_filtro}"):
                                    cursor.execute("UPDATE pedidos SET valor_total = ? WHERE id = ?", (novo_valor, ped_id))
                                    conn.commit()
                                    st.toast(f"💰 Valor atualizado — Pedido #{ped_id}", icon="✅")
                                    st.rerun()

                        with col_btns:
                            for novo_status, icone in STATUS_OPCOES:
                                if novo_status != status:
                                    if st.button(f"{icone} {novo_status}", key=f"status_{novo_status}_{ped_id}", type="secondary"):
                                        cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, ped_id))

                                        if novo_status == "Concluído" and baixado == 0:
                                            if mat_id:
                                                cursor.execute("UPDATE materiais SET quantidade_g = quantidade_g - ? WHERE id = ?", (peso, mat_id))
                                            cursor.execute("UPDATE pedidos SET estoque_baixado = 1 WHERE id = ?", (ped_id,))
                                            st.toast(f"✅ Pedido #{ped_id} CONCLUÍDO!", icon="🎉")

                                        elif novo_status != "Concluído" and baixado == 1:
                                            if mat_id:
                                                cursor.execute("UPDATE materiais SET quantidade_g = quantidade_g + ? WHERE id = ?", (peso, mat_id))
                                            cursor.execute("UPDATE pedidos SET estoque_baixado = 0 WHERE id = ?", (ped_id,))
                                            st.toast(f"↩️ Estoque estornado!", icon="🔄")

                                        conn.commit()
                                        st.rerun()

                            if status_filtro == "Cancelado":
                                if st.button("🗑️ Excluir", key=f"excluir_ped_{ped_id}", type="secondary"):
                                    cursor.execute("DELETE FROM pedidos WHERE id = ?", (ped_id,))
                                    conn.commit()
                                    st.toast(f"🗑️ Pedido #{ped_id} excluído!", icon="⚠️")
                                    st.rerun()
    else:
        icone_msg = status_icones.get(status_filtro, "📭")
        st.markdown(f"""
        <div style="background: rgba(96,165,250,0.08); border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:2rem; text-align:center; backdrop-filter:blur(12px); margin:1rem 0;">
            <div style="font-size:2.5rem;">{icone_msg}</div>
            <div style="font-size:1.05rem; color:#e5e7eb;">Nenhum pedido com status <strong>{status_filtro}</strong></div>
        </div>
        """, unsafe_allow_html=True)