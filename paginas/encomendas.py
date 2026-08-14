import streamlit as st

def render_encomendas(conn, cursor):
    # 1. Título Corrigido
    st.title("💡 Ideias Personalizadas")
    st.caption("Gerencie solicitações de peças customizadas, buscas de arquivos STL e orçamentos em análise.")

    # Tabela no banco de dados para Ideias Personalizadas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ideias_personalizadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        cliente_nome TEXT NOT NULL,
        descricao TEXT NOT NULL,
        referencia_link TEXT,
        prioridade TEXT DEFAULT 'Média',
        status TEXT DEFAULT '🟡 Procurando STL',
        observacoes TEXT,
        data_registro DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

    # 2. Formulário de Cadastro Rápido
    with st.expander("➕ Cadastrar Nova Ideia", expanded=False):
        cursor.execute("SELECT id, nome FROM clientes ORDER BY nome ASC")
        clientes = cursor.fetchall()
        lista_clientes = [f"{c[0]} - {c[1]}" for c in clientes]
        lista_clientes.insert(0, "➕ Cadastrar Novo Cliente / Digitar Nome")

        col1, col2 = st.columns(2)
        with col1:
            cli_sel = st.selectbox("Cliente*", lista_clientes)
            
            # Se for novo cliente, abre o campo de texto sem apagar
            cli_nome_manual = ""
            if cli_sel == "➕ Cadastrar Novo Cliente / Digitar Nome":
                cli_nome_manual = st.text_input("Nome do Novo Cliente*", placeholder="Ex: João da Silva")

            descricao = st.text_input("O que o cliente quer?*", placeholder="Ex: Boneco Homem de Ferro 15cm, Peça do Gol 94...")
            prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "🚨 Urgente"])

        with col2:
            ref_link = st.text_input("Link ou Foto de Referência (Opcional)", placeholder="https://makerworld.com/...")
            status_inicial = st.selectbox("Status Inicial", [
                "🟡 Procurando STL",
                "🔵 Aguardando Modelagem 3D",
                "🟠 Orçamento Enviado",
                "🔴 Inviável / Recusado"
            ])
            obs = st.text_area("Observações / Detalhes", placeholder="Ex: Quer na cor preta, aniversário dia 20...")

        if st.button("💾 Salvar Ideia", use_container_width=True):
            if not descricao:
                st.error("Preencha a descrição do pedido!")
            else:
                cli_id = None
                cli_nome = ""

                if cli_sel == "➕ Cadastrar Novo Cliente / Digitar Nome":
                    cli_nome = cli_nome_manual.strip() if cli_nome_manual else "Cliente Não Identificado"
                else:
                    cli_id = int(cli_sel.split(" - ")[0])
                    cli_nome = cli_sel.split(" - ")[1]

                cursor.execute("""
                    INSERT INTO ideias_personalizadas (cliente_id, cliente_nome, descricao, referencia_link, prioridade, status, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (cli_id, cli_nome, descricao, ref_link, prioridade, status_inicial, obs))
                conn.commit()
                st.success("Ideia salva com sucesso!")
                st.rerun()

    st.divider()

    # 3. Visualização e Gestão das Ideias
    st.subheader("📌 Quadros de Ideias")

    cursor.execute("""
        SELECT id, cliente_nome, descricao, referencia_link, prioridade, status, observacoes, data_registro
        FROM ideias_personalizadas
        WHERE status != '🟢 Aprovado (Enviado p/ Fila)'
        ORDER BY id DESC
    """)
    ideias = cursor.fetchall()

    if not ideias:
        st.info("Nenhuma ideia personalizada pendente no momento!")
    else:
        for item in ideias:
            i_id, cli_nome, desc, ref, prio, status, obs, data = item
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.2, 1.2, 1.2])
                
                with c1:
                    st.markdown(f"### #{i_id} - {desc}")
                    st.write(f"👤 **Cliente:** {cli_nome} | ⏳ **Data:** {data[:10] if data else 'N/A'}")
                    if ref:
                        st.markdown(f"🔗 [Link de Referência]({ref})")
                    if obs:
                        st.caption(f"📝 *{obs}*")

                with c2:
                    st.write(f"**Prioridade:** {prio}")
                    
                    opcoes_status = [
                        "🟡 Procurando STL",
                        "🔵 Aguardando Modelagem 3D",
                        "🟠 Orçamento Enviado",
                        "🟢 Aprovado (Mover p/ Fila)",
                        "🔴 Inviável / Recusado"
                    ]
                    
                    idx_atual = opcoes_status.index(status) if status in opcoes_status else 0
                    novo_status = st.selectbox(
                        "Alterar Status",
                        opcoes_status,
                        index=idx_atual,
                        key=f"status_{i_id}"
                    )

                    if novo_status != status and novo_status != "🟢 Aprovado (Mover p/ Fila)":
                        cursor.execute("UPDATE ideias_personalizadas SET status = ? WHERE id = ?", (novo_status, i_id))
                        conn.commit()
                        st.rerun()

                with c3:
                    st.write("---")
                    # Se o status selecionado for Aprovado, exibe o form para lançar direto nos Pedidos
                    if novo_status == "🟢 Aprovado (Mover p/ Fila)":
                        st.success("Aprovado! Preencha para enviar:")
                        with st.popover("🚀 Criar Pedido Agora"):
                            val_total = st.number_input("Valor Fechado (R$)", min_value=0.0, value=50.0, step=5.0, key=f"v_{i_id}")
                            peso_est = st.number_input("Peso Est. (g)", min_value=0.0, value=100.0, step=10.0, key=f"p_{i_id}")
                            tempo_est = st.number_input("Tempo Est. (h)", min_value=0.0, value=2.0, step=0.5, key=f"t_{i_id}")
                            
                            if st.button("✅ Confirmar e Ir p/ Fila", key=f"btn_mvr_{i_id}"):
                                # ✅ CORRIGIDO: quantidade de campos = quantidade de valores
                                cursor.execute("""
                                    INSERT INTO pedidos (cliente, nome_peca, peso_g, tempo_h, valor_total, status, data_criado)
                                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                                """, (cli_nome, desc, peso_est, tempo_est, val_total, "Pendente"))
                                
                                # Atualiza o status da Ideia
                                cursor.execute("UPDATE ideias_personalizadas SET status = '🟢 Aprovado (Enviado p/ Fila)' WHERE id = ?", (i_id,))
                                conn.commit()
                                st.success("Pedido gerado na Fila de Pedidos!")
                                st.rerun()

                    if st.button("🗑️ Excluir", key=f"del_{i_id}", use_container_width=True):
                        cursor.execute("DELETE FROM ideias_personalizadas WHERE id = ?", (i_id,))
                        conn.commit()
                        st.rerun()