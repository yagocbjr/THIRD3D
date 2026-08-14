import base64
import io
import os
import re
from PIL import Image, ImageDraw, ImageFont
import streamlit as st


def carregar_imagem_peca(img_input):
    """Auxiliar para converter a imagem da peça (caminho, base64 ou bytes) em objeto PIL Image."""
    if not img_input:
        return None
    try:
        if isinstance(img_input, str):
            if img_input.startswith("data:image"):
                base64_data = re.sub("^data:image/.+;base64,", "", img_input)
                img_bytes = base64.b64decode(base64_data)
                return Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            elif os.path.exists(img_input):
                return Image.open(img_input).convert("RGBA")
        elif isinstance(img_input, bytes):
            return Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    except Exception:
        pass
    return None


def gerar_imagem_orcamento(
    cliente, carrinho, subtotal_peso, subtotal_tempo, ajuste, total_final
):
    # Dimensões para formato Portrait (Vertical para celular)
    largura = 500
    altura_base = 260
    altura_itens = sum(70 if item.get("imagem") else 55 for item in carrinho)
    altura = altura_base + altura_itens

    img = Image.new("RGB", (largura, altura), color=(20, 24, 33))
    draw = ImageDraw.Draw(img)

    try:
        fonte_titulo = ImageFont.truetype("arial.ttf", 20)
        fonte_sub = ImageFont.truetype("arial.ttf", 15)
        fonte_texto = ImageFont.truetype("arial.ttf", 13)
        fonte_bold = ImageFont.truetype("arialbd.ttf", 14)
        fonte_destaque = ImageFont.truetype("arialbd.ttf", 18)
    except OSError:
        fonte_titulo = (
            fonte_sub
        ) = fonte_texto = fonte_bold = fonte_destaque = ImageFont.load_default()

    x_offset = 25
    if os.path.exists("logo.png"):
        try:
            logo = Image.open("logo.png").convert("RGBA")
            logo.thumbnail((55, 55))
            # Tratamento de máscara alfa para evitar ValueError
            img.paste(logo, (25, 20), logo if logo.mode == "RGBA" else None)
            x_offset = 90
        except Exception:
            pass

    # Cabeçalho
    draw.text(
        (x_offset, 22),
        "ORÇAMENTO IMPRESSÃO 3D",
        fill=(255, 255, 255),
        font=fonte_titulo,
    )
    nome_cli = cliente.strip() if cliente and cliente.strip() else "Não informado"
    draw.text(
        (x_offset, 50),
        f"Cliente: {nome_cli}",
        fill=(0, 180, 255),
        font=fonte_sub,
    )

    draw.line([(25, 90), (largura - 25, 90)], fill=(60, 70, 90), width=2)

    # Itens do Carrinho
    y = 105
    draw.text(
        (25, y), "ITENS DO PEDIDO:", fill=(160, 170, 190), font=fonte_bold
    )
    y += 28

    for item in carrinho:
        mat = item.get("material_nome", "").strip()
        nome_peca = item["nome"]

        # Truncar nome se for muito grande
        if len(nome_peca) > 35:
            nome_peca = nome_peca[:32] + "..."

        img_peca = carregar_imagem_peca(item.get("imagem"))
        x_texto = 25

        if img_peca:
            img_peca.thumbnail((45, 45))
            img.paste(img_peca, (25, y), img_peca if img_peca.mode == "RGBA" else None)
            x_texto = 80

        # Linha 1 do Item
        draw.text(
            (x_texto, y),
            nome_peca,
            fill=(255, 255, 255),
            font=fonte_bold,
        )
        y_item = y + 18

        # Linha 2 do Item
        if mat:
            draw.text(
                (x_texto, y_item),
                f"[{mat}]",
                fill=(170, 180, 200),
                font=fonte_texto,
            )
            y_item += 18

        # Linha 3 do Item
        detalhes = f"R$ {item['valor']:.2f}  |  {item['peso']:.0f}g  |  {item['tempo']:.1f}h"
        draw.text(
            (x_texto, y_item),
            detalhes,
            fill=(130, 140, 160),
            font=fonte_texto,
        )

        y += 70 if img_peca else 55

    draw.line([(25, y), (largura - 25, y)], fill=(60, 70, 90), width=1)
    y += 15

    # Resumo Geral Final
    if ajuste != 0:
        draw.text(
            (25, y),
            f"Ajuste / Taxa: R$ {ajuste:+.2f}",
            fill=(255, 190, 0),
            font=fonte_texto,
        )
        y += 22

    draw.text(
        (25, y),
        f"Totais: {subtotal_peso:.0f}g  |  {subtotal_tempo:.1f}h de máquina",
        fill=(170, 180, 200),
        font=fonte_texto,
    )
    y += 26

    draw.text(
        (25, y),
        f"VALOR TOTAL: R$ {total_final:.2f}",
        fill=(80, 220, 100),
        font=fonte_destaque,
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def render_calculadora(conn, cursor):
    st.title("🛒 Calculadora & Carrinho")  # <--- Altere essa linha aqui!

    cursor.execute("""
        SELECT m.id, mc.nome, m.cor, m.tipo, m.preco_kg, m.nome
        FROM materiais m
        LEFT JOIN marcas mc ON m.marca_id = mc.id
    """)
    ...

    # FIX 1: Inicializar estado do carrinho
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    cursor.execute("""
        SELECT m.id, mc.nome, m.cor, m.tipo, m.preco_kg, m.nome
        FROM materiais m
        LEFT JOIN marcas mc ON m.marca_id = mc.id
    """)
    materiais_cadastrados = cursor.fetchall()

    if not materiais_cadastrados:
        st.warning(
            "⚠️ Cadastre materiais no estoque antes de realizar orçamentos!"
        )
        return

    col_esq, col_dir = st.columns([1, 1])

    with col_esq:
        st.subheader("1. Adicionar Peça")
        origem_peca = st.radio(
            "Origem da Peça:",
            ["🧩 Escolher do Catálogo", "✏️ Calcular Peça Avulsa"],
            horizontal=True,
        )

        if origem_peca == "🧩 Escolher do Catálogo":
            cursor.execute("""
                SELECT p.id, p.nome_peca, mc.nome, m.cor, m.tipo, p.peso_g, p.tempo_h, p.preco_sugerido, p.imagem, p.material_id
                FROM pecas_padrao p
                LEFT JOIN materiais m ON p.material_id = m.id
                LEFT JOIN marcas mc ON m.marca_id = mc.id
            """)
            pecas_cadastradas = cursor.fetchall()

            if pecas_cadastradas:
                dict_pecas = {
                    f"{p[1]} ({p[2] or ''} - {p[3] or ''}) - Sugerido: R$ {p[7]:.2f}": p
                    for p in pecas_cadastradas
                }
                peca_selecionada_nome = st.selectbox(
                    "Selecione a Peça Padrão:", list(dict_pecas.keys())
                )
                peca_dados = dict_pecas[peca_selecionada_nome]

                (
                    p_id,
                    p_nome,
                    mc_nome,
                    m_cor,
                    m_tipo,
                    p_peso,
                    p_tempo,
                    p_preco,
                    p_imagem,
                    mat_id,
                ) = peca_dados

                col_q1, col_q2 = st.columns(2)
                with col_q1:
                    qtd = st.number_input(
                        "Quantidade", min_value=1, value=1, step=1
                    )
                with col_q2:
                    preco_venda_unit = st.number_input(
                        "Preço de Venda Final (R$)*",
                        value=float(p_preco),
                        step=1.0,
                    )

                peso_total = float(p_peso) * qtd
                tempo_total = float(p_tempo) * qtd
                preco_venda_total = float(preco_venda_unit) * qtd
                mat_str = f"{mc_nome or ''} - {m_cor or ''} ({m_tipo or ''})"

                st.caption(
                    f"Peso: **{peso_total:.1f}g** | Tempo: **{tempo_total:.1f}h** | Valor Sugerido: ~~R$ {p_preco * qtd:.2f}~~"
                )

                if st.button("➕ Adicionar ao Carrinho", type="primary"):
                    st.session_state.carrinho.append({
                        "nome": (
                            p_nome if qtd == 1 else f"{p_nome} (x{qtd})"
                        ),
                        "peso": peso_total,
                        "tempo": tempo_total,
                        "valor": preco_venda_total,
                        "material_nome": mat_str,
                        "material_id": mat_id,
                        "imagem": p_imagem,
                    })
                    st.toast("Item adicionado ao carrinho!", icon="🛒")
                    st.rerun()
            else:
                st.warning("Nenhuma peça cadastrada no catálogo ainda.")

        else:
            dict_mats = {
                f"{m[1] or ''} - {m[2] or ''} ({m[3] or ''}) (R$ {m[4]:.2f}/Kg)": m
                for m in materiais_cadastrados
            }
            mat_escolhido = st.selectbox("Filamento:", list(dict_mats.keys()))
            mat_dados = dict_mats[mat_escolhido]

            v_item_mat_id = mat_dados[0]
            preco_filamento_kg = float(mat_dados[4])

            v_item_nome = st.text_input("Nome da Peça Avulsa", value="")

            c_a, c_b = st.columns(2)
            with c_a:
                peso_g = st.number_input(
                    "Peso (g)", min_value=0.1, value=50.0, step=10.0
                )
                horas_impressao = st.number_input(
                    "Tempo (Horas)", min_value=0.0, value=2.0, step=0.5
                )
            with c_b:
                custo_hora_maquina = st.number_input(
                    "Custo Hora (R$)", min_value=0.0, value=2.50, step=0.50
                )
                margem_lucro = st.number_input(
                    "Margem (%)", min_value=0.0, value=100.0, step=10.0
                )

            v_c_mat = (peso_g / 1000.0) * preco_filamento_kg
            v_c_maq = horas_impressao * custo_hora_maquina
            v_calc = (v_c_mat + v_c_maq) * (1.0 + (margem_lucro / 100.0))

            preco_avulso_negociado = st.number_input(
                "Preço Final Ajustado (R$)*",
                min_value=0.0,
                value=float(v_calc),
                step=1.0,
            )

            if st.button("➕ Adicionar Peça Avulsa ao Carrinho", type="primary"):
                if v_item_nome.strip():
                    # Extração mais segura do nome do material
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
                    st.toast(
                        f"'{v_item_nome}' adicionado ao carrinho!",
                        icon="🛒",
                    )
                    st.rerun()
                else:
                    st.error("Digite o nome da peça avulsa.")

    with col_dir:
        st.subheader("2. Resumo do Pedido (Carrinho)")

        if not st.session_state.carrinho:
            st.info("Seu carrinho está vazio. Adicione itens do lado esquerdo.")
        else:
            subtotal_peso = sum(item["peso"] for item in st.session_state.carrinho)
            subtotal_tempo = sum(item["tempo"] for item in st.session_state.carrinho)
            subtotal_valor = sum(item["valor"] for item in st.session_state.carrinho)

            for idx, item in enumerate(st.session_state.carrinho):
                with st.container(border=True):
                    c_img, c_i1, c_i2 = st.columns([1, 3, 0.8])

                    with c_img:
                        if item.get("imagem"):
                            st.image(item["imagem"], width=60)
                        else:
                            st.caption("🖼️ Sem foto")

                    with c_i1:
                        mat_nome = item.get(
                            "material_nome", item.get("material_cor", "")
                        )
                        st.write(f"**{item['nome']}** ({mat_nome})")
                        st.caption(
                            f"Peso: {item['peso']:.1f}g | Tempo: {item['tempo']:.1f}h | Valor: **R$ {item['valor']:.2f}**"
                        )

                    with c_i2:
                        if st.button("❌", key=f"remover_item_{idx}"):
                            st.session_state.carrinho.pop(idx)
                            st.rerun()

            st.divider()

            ajuste_global = st.number_input(
                "Ajuste Geral no Pedido (R$) (+ para Taxa / - para Desconto):*",
                value=0.0,
                step=5.0,
            )

            total_final_pedido = max(0.0, subtotal_valor + ajuste_global)

            st.metric(
                "Total Final do Pedido",
                f"R$ {total_final_pedido:.2f}",
                delta=f"{subtotal_peso:.0f}g | {subtotal_tempo:.1f}h total",
            )

            st.subheader("3. Cliente e Finalização")
            cursor.execute("SELECT nome FROM clientes ORDER BY nome ASC")
            clientes_cadastrados = [c[0] for c in cursor.fetchall()]

            if clientes_cadastrados:
                opcoes_cliente = ["-- Digitar Nome Manualmente --"] + clientes_cadastrados
                cli_selecionado = st.selectbox("Selecione o Cliente:*", opcoes_cliente)

                if cli_selecionado == "-- Digitar Nome Manualmente --":
                    cliente_final = st.text_input("Nome do Cliente*", value="")
                else:
                    cliente_final = cli_selecionado
            else:
                cliente_final = st.text_input("Nome do Cliente*", value="")

            # FIX 2 & 3: Geração e Download Contínuos sem Sumir da Tela
            st.write("---")
            
            # Botão para gerar a imagem
            if st.button("🖼️ Gerar/Atualizar Imagem do Orçamento", use_container_width=True):
                buf_img = gerar_imagem_orcamento(
                    cliente_final.strip(),
                    st.session_state.carrinho,
                    subtotal_peso,
                    subtotal_tempo,
                    ajuste_global,
                    total_final_pedido,
                )
                st.session_state["buf_orcamento"] = buf_img.getvalue()

            # Se a imagem já foi gerada, ela permanece visível na tela mesmo se a página recarregar
            if "buf_orcamento" in st.session_state:
                st.image(
                    st.session_state["buf_orcamento"],
                    caption="Prévia do Orçamento",
                    use_container_width=True,
                )

                nome_limpo = (
                    cliente_final.strip().lower().replace(" ", "_")
                    if cliente_final.strip()
                    else "cliente"
                )
                
                st.download_button(
                    label="📥 Baixar Imagem do Orçamento (.png)",
                    data=st.session_state["buf_orcamento"],
                    file_name=f"orcamento_{nome_limpo}.png",
                    mime="image/png",
                    use_container_width=True,
                )

            st.write("---")

            if st.button(
                "📜 Finalizar e Criar Pedido",
                type="primary",
                use_container_width=True,
            ):
                if cliente_final.strip():
                    resumo_pecas = " + ".join([
                        item["nome"] for item in st.session_state.carrinho
                    ])
                    if ajuste_global != 0:
                        resumo_pecas += f" (Ajuste: R$ {ajuste_global:+.2f})"

                    primeiro_material_id = st.session_state.carrinho[0]["material_id"]

                    cursor.execute(
                        """
                        INSERT INTO pedidos (cliente, nome_peca, material_id, peso_g, tempo_h, valor_total, status, data_criado)
    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """,
                        (
                            cliente_final.strip(),
                            resumo_pecas,
                            primeiro_material_id,
                            subtotal_peso,
                            subtotal_tempo,
                            total_final_pedido,
                            "Pendente",

                        ),
                    )
                    conn.commit()

                    # Limpa carrinho e imagem gerada após salvar pedido
                    st.session_state.carrinho = []
                    if "buf_orcamento" in st.session_state:
                        del st.session_state["buf_orcamento"]

                    st.success("Pedido criado com sucesso!")
                    st.rerun()
                else:
                    st.error("Informe o Nome do Cliente para finalizar o pedido.")