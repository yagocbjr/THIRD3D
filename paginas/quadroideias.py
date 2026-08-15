import streamlit as st

def render_quadro_ideias(conn, cursor):
    st.title("📋 Quadro de Ideias — Gestão Interna")
    st.caption("Acompanhamento e gerenciamento de solicitações de clientes")

    # ✅ GARANTE QUE TODAS AS COLUNAS EXISTEM
    try:
        cursor.execute("ALTER TABLE ideias_personalizadas ADD COLUMN telefone TEXT")
        conn.commit()
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE ideias_personalizadas ADD COLUMN prioridade TEXT DEFAULT 'Média'")
        conn.commit()
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE ideias_personalizadas ADD COLUMN status TEXT DEFAULT '🟡 Procurando STL'")
        conn.commit()
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE ideias_personalizadas ADD COLUMN observacoes TEXT")
        conn.commit()
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE ideias_personalizadas ADD COLUMN data_registro DATETIME DEFAULT CURRENT_TIMESTAMP")
        conn.commit()
    except Exception:
        pass

    # ✅ Busca todas as ideias — com tratamento seguro de colunas
    cursor.execute("""
        SELECT id, cliente_nome, 
               COALESCE(telefone, '') as telefone, 
               descricao, 
               COALESCE(referencia_link, '') as referencia_link, 
               COALESCE(imagem, '') as imagem,
               COALESCE(prioridade, 'Média') as prioridade, 
               COALESCE(status, '🟡 Procurando STL') as status, 
               COALESCE(observacoes, '') as observacoes, 
               COALESCE(data_registro, datetime('now')) as data_registro
        FROM ideias_personalizadas
        WHERE status != '🟢 Aprovado (Enviado p/ Fila)' OR status IS NULL
        ORDER BY id DESC
    """)
    ideias = cursor.fetchall()

    if not ideias:
        st.info("✅ Nenhuma solicitação pendente!")
        return

    # Exibe cada ideia
    for item in ideias:
        i_id, cli_nome, fone, desc, ref, imagem, prio, status, obs, data = item

        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 1, 1])

            with c1:
                st.markdown(f"### #{i_id} - {cli_nome}")
                st.write(f"📞 **Telefone:** {fone or 'Não informado'}")
                st.write(f"📝 **Solicitação:** {desc}")
                if imagem:
                    st.image(imagem, width=200, caption="Foto enviada pelo cliente")
                if ref:
                    st.markdown(f"🔗 [Link de Referência]({ref})")
                st.caption(f"📅 Data: {data[:10] if data else 'N/A'}")
                if obs:
                    st.info(f"📌 Observações: {obs}")

            with c2:
                st.subheader("Controle Interno")
                opcoes_prio = ["Baixa", "Média", "Alta", "🚨 Urgente"]
                idx_prio = opcoes_prio.index(prio) if prio in opcoes_prio else 1
                prio_novo = st.selectbox("Prioridade", opcoes_prio, index=idx_prio, key=f"prio_{i_id}")

                opcoes_status = [
                    "🟡 Procurando STL",
                    "🔵 Aguardando Modelagem 3D",
                    "🟠 Orçamento Enviado",
                    "🟢 Aprovado (Mover p/ Fila)",
                    "🔴 Inviável / Recusado"
                ]
                idx_atual = opcoes_status.index(status) if status in opcoes_status else 0
                novo_status = st.selectbox("Status", opcoes_status, index=idx_atual, key=f"status_{i_id}")

                obs_novo = st.text_area("Anotações", value=obs or "", key=f"obs_{i_id}", height=80)

                if st.button("💾 Salvar", key=f"salvar_{i_id}"):
                    cursor.execute("""
                        UPDATE ideias_personalizadas 
                        SET prioridade = ?, status = ?, observacoes = ?
                        WHERE id = ?
                    """, (prio_novo, novo_status, obs_novo, i_id))
                    conn.commit()
                    st.success("✅ Salvo!")
                    st.rerun()

            with c3:
                st.write("---")
                if novo_status == "🟢 Aprovado (Mover p/ Fila)":
                    st.success("✅ Aprovado → Enviar para Pedidos")
                    with st.popover("🚀 Criar Pedido"):
                        val_total = st.number_input("Valor (R$)", min_value=0.0, value=50.0, step=5.0, key=f"v_{i_id}")
                        peso_est = st.number_input("Peso (g)", min_value=0.0, value=100.0, step=10.0, key=f"p_{i_id}")
                        tempo_est = st.number_input("Tempo (h)", min_value=0.0, value=2.0, step=0.5, key=f"t_{i_id}")
                        
                        if st.button("✅ Confirmar", key=f"btn_{i_id}"):
                            cursor.execute("""
                                INSERT INTO pedidos (cliente, nome_peca, peso_g, tempo_h, valor_total, status, data_criado)
                                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                            """, (cli_nome, desc, peso_est, tempo_est, val_total, "Pendente"))
                            cursor.execute("UPDATE ideias_personalizadas SET status = '🟢 Aprovado (Enviado p/ Fila)' WHERE id = ?", (i_id,))
                            conn.commit()
                            st.success("✅ Pedido criado!")
                            st.rerun()

                if st.button("🗑️ Excluir", key=f"del_{i_id}", use_container_width=True):
                    cursor.execute("DELETE FROM ideias_personalizadas WHERE id = ?", (i_id,))
                    conn.commit()
                    st.rerun()
