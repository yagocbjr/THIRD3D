import pandas as pd
import plotly.express as px
import streamlit as st


def render_faturamento(conn, cursor):
    st.title("💰 Faturamento & Análise Financeira")
    st.caption("Acompanhamento de valores, custos e lucro dos pedidos concluídos.")

    # 🔒 SENHA DE ACESSO
    SENHA_ACESSO = "1234"  # ✅ ALTERE AQUI PARA SUA SENHA!

    if "acesso_faturamento" not in st.session_state:
        st.session_state.acesso_faturamento = False

    if not st.session_state.acesso_faturamento:
        st.warning("🔒 Esta página é protegida por senha.")
        senha_digitada = st.text_input("Digite a senha de acesso:", type="password")
        if st.button("🔓 Desbloquear"):
            if senha_digitada == SENHA_ACESSO:
                st.session_state.acesso_faturamento = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
        st.stop()

    st.success("🔓 Acesso liberado!")
    st.divider()

    # 📅 PERÍODO
    st.subheader("📅 Período")
    col_dti, col_dtf = st.columns(2)
    with col_dti:
        data_inicio = st.date_input("Data Inicial", key="fat_data_inicio")
    with col_dtf:
        data_fim = st.date_input("Data Final", key="fat_data_fim")

    # ✅ CUSTO HORA REMOVIDO — VALOR FIXO AQUI
    custo_hora = 2.50

    st.divider()

    # ✅ FILTRO CORRIGIDO E SEGURO
    data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT p.id, p.cliente, p.nome_peca, p.peso_g, p.tempo_h, p.valor_total, 
               p.data_criado, m.preco_kg
        FROM pedidos p
        LEFT JOIN materiais m ON p.material_id = m.id
        WHERE p.status = 'Concluído'
          AND SUBSTR(p.data_criado, 1, 10) >= ?
          AND SUBSTR(p.data_criado, 1, 10) <= ?
        ORDER BY p.id DESC
    """, (data_inicio_str, data_fim_str))

    pedidos_concluidos = cursor.fetchall()

    if pedidos_concluidos:
        tot_fat = 0.0
        tot_custo = 0.0
        analise_pedidos = []

        for ped in pedidos_concluidos:
            p_id, cli, peca, peso, tempo, valor, data_criado, preco_kg = ped
            preco_kg = preco_kg or 110.0

            c_mat = (peso / 1000.0) * preco_kg
            c_maq = tempo * custo_hora
            c_total = c_mat + c_maq
            lucro = valor - c_total

            tot_fat += valor
            tot_custo += c_total

            analise_pedidos.append({
                "ID": f"#{p_id}",
                "Data": data_criado[:10] if data_criado else "---",
                "Cliente": cli,
                "Peça": peca,
                "Valor Cobrado": f"R$ {valor:.2f}",
                "Custo Prod.": f"R$ {c_total:.2f}",
                "Lucro Líquido": f"R$ {lucro:.2f}",
            })

        lucro_geral = max(0.0, tot_fat - tot_custo)
        margem = (lucro_geral / tot_fat * 100) if tot_fat > 0 else 0

        st.subheader("📊 Resumo do Período")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("💵 Faturamento Total", f"R$ {tot_fat:.2f}")
        with r2:
            st.metric("💸 Custo Total", f"R$ {tot_custo:.2f}")
        with r3:
            st.metric("💚 Lucro Líquido", f"R$ {lucro_geral:.2f}",
                      delta=f"{margem:.1f}% de margem")

        st.divider()

        col_tabela, col_grafico = st.columns([1.2, 1])
        with col_tabela:
            st.subheader("📋 Detalhamento por Pedido")
            st.dataframe(analise_pedidos, use_container_width=True, hide_index=True)

        with col_grafico:
            st.subheader("📈 Custo x Lucro")
            df_plot = pd.DataFrame({
                "Categoria": ["Custo", "Lucro Líquido"],
                "Valor": [tot_custo, lucro_geral],
            })
            fig = px.pie(
                df_plot,
                names="Categoria",
                values="Valor",
                color="Categoria",
                color_discrete_map={"Custo": "#FF4B4B", "Lucro Líquido": "#2ECC71"},
                hole=0.5,
            )
            fig.update_traces(textinfo="percent")
            fig.update_layout(
                showlegend=True,
                margin=dict(l=10, r=10, t=30, b=10),
                height=320,
                legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info(f"📋 Nenhum pedido concluído encontrado entre {data_inicio_str} e {data_fim_str}.")