import streamlit as st


def render_dashboard(conn, cursor):
    st.title("📊 Visão Geral de Pedidos")
    st.caption("Acompanhamento rápido de status e quantidades.")
    st.divider()

    # --- BUSCA DE DADOS ---
    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'Pendente'")
    qtd_pendente = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'Imprimindo'")
    qtd_imprimindo = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'Concluído'")
    qtd_concluidos = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'Arquivado'")
    qtd_arquivado = cursor.fetchone()[0] or 0

    total_geral = qtd_pendente + qtd_imprimindo + qtd_concluidos + qtd_arquivado

    # --- BOTÕES GRANDES COLORIDOS ---
    st.subheader("📋 Status dos Pedidos")
    st.write("")  # Espaçamento

    b1, b2, b3, b4 = st.columns(4)

    estilo_botao = """
    <style>
    .botao-status {
        padding: 20px 10px;
        border-radius: 12px;
        text-align: center;
        font-size: 26px;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .botao-pendente { background-color: #FFF3CD; color: #856404; }
    .botao-imprimindo { background-color: #F8D7DA; color: #721C24; }
    .botao-concluido { background-color: #D4EDDA; color: #155724; }
    .botao-arquivado { background-color: #E2E3E5; color: #383D41; }
    .botao-icone { font-size: 32px; margin-bottom: 5px; }
    .botao-texto { font-size: 14px; font-weight: normal; opacity: 0.8; }
    </style>
    """
    st.markdown(estilo_botao, unsafe_allow_html=True)

    with b1:
        st.markdown(f"""
        <div class="botao-status botao-pendente">
            <div class="botao-icone">🟡</div>
            {qtd_pendente}
            <div class="botao-texto">Pendentes</div>
        </div>
        """, unsafe_allow_html=True)

    with b2:
        st.markdown(f"""
        <div class="botao-status botao-imprimindo">
            <div class="botao-icone">🔴</div>
            {qtd_imprimindo}
            <div class="botao-texto">Imprimindo</div>
        </div>
        """, unsafe_allow_html=True)

    with b3:
        st.markdown(f"""
        <div class="botao-status botao-concluido">
            <div class="botao-icone">✅</div>
            {qtd_concluidos}
            <div class="botao-texto">Concluídos</div>
        </div>
        """, unsafe_allow_html=True)

    with b4:
        st.markdown(f"""
        <div class="botao-status botao-arquivado">
            <div class="botao-icone">📦</div>
            {qtd_arquivado}
            <div class="botao-texto">Arquivados</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- TOTAL GERAL ---
    st.info(f"📊 **Total de Pedidos Registrados:** {total_geral} pedido(s)")

    st.divider()

    # --- PEDIDOS EM ANDAMENTO ---
    st.subheader("📋 Pedidos em Andamento")
    cursor.execute("""
        SELECT p.id, p.cliente, p.nome_peca, p.tempo_h, p.status, p.data_criado
        FROM pedidos p
        WHERE p.status IN ('Pendente', 'Imprimindo')
        ORDER BY p.status DESC, p.id DESC
    """)
    pedidos_ativos = cursor.fetchall()

    if pedidos_ativos:
        lista_ped_exibir = []
        for p in pedidos_ativos:
            lista_ped_exibir.append({
                "ID": f"#{p[0]}",
                "Cliente": p[1],
                "Peça": p[2],
                "Status": "🔴 Imprimindo" if p[4] == "Imprimindo" else "🟡 Pendente",
                "Tempo Est.": f"{p[3]:.1f} h",
                "Data": p[5][:10] if p[5] else "---",
            })
        st.dataframe(lista_ped_exibir, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Nenhum pedido em andamento no momento!")

    st.divider()

    # --- ÚLTIMOS CONCLUÍDOS ---
    st.subheader("✅ Últimos Pedidos Concluídos")
    cursor.execute("""
        SELECT p.id, p.cliente, p.nome_peca, p.tempo_h, p.data_criado
        FROM pedidos p
        WHERE p.status = 'Concluído'
        ORDER BY p.id DESC
        LIMIT 10
    """)
    ultimos_concluidos = cursor.fetchall()

    if ultimos_concluidos:
        lista_ultimos = []
        for p in ultimos_concluidos:
            lista_ultimos.append({
                "ID": f"#{p[0]}",
                "Cliente": p[1],
                "Peça": p[2],
                "Tempo Est.": f"{p[3]:.1f} h",
                "Data": p[4][:10] if p[4] else "---",
            })
        st.dataframe(lista_ultimos, use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não há pedidos concluídos.")