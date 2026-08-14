import streamlit as st

def render_clientes(conn, cursor):
    st.title("👤 Gestão de Clientes")

    with st.expander("➕ Cadastrar Novo Cliente", expanded=True):
        with st.form("form_cliente", clear_on_submit=True):
            col_cli1, col_cli2 = st.columns(2)
            with col_cli1:
                nome_cli = st.text_input("Nome Completo do Cliente*")
                tel_cli = st.text_input("WhatsApp / Telefone (opcional)")
            with col_cli2:
                obs_cli = st.text_area("Observações (ex: Preferência de entrega, endereço)")

            if st.form_submit_button("Salvar Cliente"):
                if nome_cli.strip():
                    cursor.execute(
                        "INSERT INTO clientes (nome, telefone, observacoes) VALUES (?, ?, ?)",
                        (nome_cli.strip(), tel_cli.strip(), obs_cli.strip())
                    )
                    conn.commit()
                    st.success(f"Cliente '{nome_cli}' cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("Por favor, preencha o nome do cliente.")

    st.divider()
    st.subheader("Clientes Cadastrados")

    cursor.execute("SELECT id, nome, telefone, observacoes FROM clientes ORDER BY nome ASC")
    lista_clientes = cursor.fetchall()

    if lista_clientes:
        st.dataframe(
            lista_clientes,
            column_config={
                "0": "ID",
                "1": "Nome",
                "2": "Telefone / WhatsApp",
                "3": "Observações",
            },
            use_container_width=True
        )

        st.subheader("⚙️ Gerenciar Cliente")
        dict_cli_gerenciar = {f"ID #{c[0]} - {c[1]}": c for c in lista_clientes}
        cli_escolhido = st.selectbox("Selecione um cliente para editar ou excluir:", list(dict_cli_gerenciar.keys()))
        
        c_id, c_nome, c_tel, c_obs = dict_cli_gerenciar[cli_escolhido]

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            with st.popover("✏️ Editar este cliente"):
                st.write(f"Editando: **{c_nome}**")
                e_nome = st.text_input("Novo Nome", value=c_nome)
                e_tel = st.text_input("Novo Telefone", value=c_tel or "")
                e_obs = st.text_area("Novas Observações", value=c_obs or "")

                if st.button("Salvar Alterações do Cliente"):
                    cursor.execute("""
                        UPDATE clientes 
                        SET nome = ?, telefone = ?, observacoes = ?
                        WHERE id = ?
                    """, (e_nome, e_tel, e_obs, c_id))
                    conn.commit()
                    st.success("Cliente atualizado com sucesso!")
                    st.rerun()

        with col_e2:
            if st.button("❌ Apagar este cliente", type="primary"):
                cursor.execute("DELETE FROM clientes WHERE id = ?", (c_id,))
                conn.commit()
                st.warning(f"Cliente ID #{c_id} apagado!")
                st.rerun()
    else:
        st.info("Nenhum cliente cadastrado ainda.")
        