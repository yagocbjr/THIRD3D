import streamlit as st
import sqlite3

def render_estoque(conn, cursor, formatar_nome_material):
    st.title("📦 Estoque de Filamentos")

    col_m1, col_m2 = st.columns([1, 2])

    # Seção 1: Cadastro de Marcas
    with col_m1:
        st.subheader("🏷️ Marcas de Filamento")
        with st.form("form_marca", clear_on_submit=True):
            nova_marca = st.text_input("Cadastrar Nova Marca (ex: eSUN, SUNLU)")
            if st.form_submit_button("➕ Adicionar Marca"):
                if nova_marca.strip():
                    try:
                        cursor.execute("INSERT INTO marcas (nome) VALUES (?)", (nova_marca.strip(),))
                        conn.commit()
                        st.success(f"Marca '{nova_marca}' adicionada!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Esta marca já está cadastrada.")
                else:
                    st.error("Digite o nome da marca.")

        cursor.execute("SELECT id, nome FROM marcas ORDER BY nome ASC")
        marcas_existentes = cursor.fetchall()
        if marcas_existentes:
            st.caption("Marcas cadastradas:")
            for m_id, m_nome in marcas_existentes:
                c_a, c_b = st.columns([3, 1])
                c_a.write(f"• **{m_nome}**")
                if c_b.button("🗑️", key=f"del_marca_{m_id}"):
                    cursor.execute("DELETE FROM marcas WHERE id = ?", (m_id,))
                    conn.commit()
                    st.rerun()

    # Seção 2: Cadastro de Filamento
    with col_m2:
        st.subheader("➕ Cadastrar Novo Filamento")
        if not marcas_existentes:
            st.warning("⚠️ Cadastre ao menos uma marca ao lado antes de adicionar um filamento!")
        else:
            dict_marcas = {m[1]: m[0] for m in marcas_existentes}
            with st.form("form_material", clear_on_submit=True):
                c_f1, c_f2 = st.columns(2)
                with c_f1:
                    marca_sel = st.selectbox("Marca*", list(dict_marcas.keys()))
                    cor_input = st.text_input("Cor do Filamento* (ex: Branco, Preto, Seda Tricolor)")
                with c_f2:
                    tipo_mat = st.selectbox("Tipo de Material", ["PLA", "ABS", "PETG", "Resina", "TPU", "Outro"])
                    preco_kg = st.number_input("Preço do Quilo (R$)", min_value=0.0, step=10.0, value=110.0)

                qtd_g = st.number_input("Quantidade em Estoque (Gramas)", min_value=0.0, step=100.0, value=1000.0)

                if st.form_submit_button("💾 Salvar Filamento no Estoque"):
                    if cor_input.strip():
                        marca_id = dict_marcas[marca_sel]
                        nome_composto = f"{marca_sel} {cor_input.strip()}"
                        
                        cursor.execute("""
                            INSERT INTO materiais (nome, marca_id, cor, tipo, preco_kg, quantidade_g)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (nome_composto, marca_id, cor_input.strip(), tipo_mat, preco_kg, qtd_g))
                        conn.commit()
                        st.success("Filamento cadastrado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Por favor, preencha a cor do filamento.")

    st.divider()

    st.subheader("Filamentos em Estoque")
    cursor.execute("""
        SELECT m.id, mc.nome, m.cor, m.tipo, m.preco_kg, m.quantidade_g, m.marca_id, m.nome
        FROM materiais m
        LEFT JOIN marcas mc ON m.marca_id = mc.id
        ORDER BY mc.nome ASC, m.cor ASC
    """)
    dados_mat = cursor.fetchall()

    if dados_mat:
        tabela_exibicao = []
        for item in dados_mat:
            marca_exib = item[1] if item[1] else "Sem Marca"
            cor_exib = item[2] if item[2] else (item[7] or "N/A")
            tabela_exibicao.append({
                "ID": item[0],
                "Marca": marca_exib,
                "Cor": cor_exib,
                "Tipo": item[3],
                "Preço/Kg (R$)": f"R$ {item[4]:.2f}",
                "Estoque (g)": f"{item[5]:.0f}g"
            })
        
        st.dataframe(tabela_exibicao, use_container_width=True)

        st.subheader("⚙️ Gerenciar Material Existente")
        dict_mat_opcoes = {
            f"ID #{item[0]} - {formatar_nome_material(item[0], item[1], item[2], item[3], item[7])} ({item[5]:.0f}g)": item 
            for item in dados_mat
        }
        escolha = st.selectbox("Selecione um material para Editar ou Apagar:", list(dict_mat_opcoes.keys()))
        
        id_sel, marca_nome_sel, cor_sel, tipo_sel, preco_sel, qtd_sel, marca_id_sel, nome_antigo_sel = dict_mat_opcoes[escolha]

        col1, col2 = st.columns(2)

        with col1:
            with st.popover("✏️ Editar este material"):
                st.write(f"Editando ID #{id_sel}")
                
                if marcas_existentes:
                    lista_m_nomes = [m[1] for m in marcas_existentes]
                    idx_m = lista_m_nomes.index(marca_nome_sel) if marca_nome_sel in lista_m_nomes else 0
                    e_marca_nome = st.selectbox("Nova Marca", lista_m_nomes, index=idx_m)
                    e_marca_id = dict_marcas[e_marca_nome]
                else:
                    e_marca_id = marca_id_sel
                    e_marca_nome = marca_nome_sel or ""

                e_cor = st.text_input("Nova Cor", value=cor_sel or nome_antigo_sel or "")
                tipos = ["PLA", "ABS", "PETG", "Resina", "TPU", "Outro"]
                idx_tipo = tipos.index(tipo_sel) if tipo_sel in tipos else 0
                e_tipo = st.selectbox("Novo Tipo", tipos, index=idx_tipo)
                e_preco = st.number_input("Novo Preço/Kg (R$)", value=float(preco_sel))
                e_qtd = st.number_input("Nova Qtd em Estoque (g)", value=float(qtd_sel))

                if st.button("Salvar Alterações"):
                    nome_comp = f"{e_marca_nome} {e_cor}".strip()
                    cursor.execute("""
                        UPDATE materiais 
                        SET nome = ?, marca_id = ?, cor = ?, tipo = ?, preco_kg = ?, quantidade_g = ?
                        WHERE id = ?
                    """, (nome_comp, e_marca_id, e_cor, e_tipo, e_preco, e_qtd, id_sel))
                    conn.commit()
                    st.success("Material atualizado!")
                    st.rerun()

        with col2:
            if st.button("❌ Apagar este material", type="primary"):
                cursor.execute("DELETE FROM materiais WHERE id = ?", (id_sel,))
                conn.commit()
                st.warning(f"Material ID #{id_sel} apagado com sucesso!")
                st.rerun()
    else:
        st.info("Nenhum filamento cadastrado ainda.")
        