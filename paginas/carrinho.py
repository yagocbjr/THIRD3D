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
    cliente, telefone, endereco, carrinho, subtotal_peso, subtotal_tempo, total_final
):
    # Formato Portrait (vertical)
    largura = 420
    altura_base = 380
    altura_itens = sum(70 if item.get("imagem") else 55 for item in carrinho)
    altura = max(altura_base + altura_itens, int(largura * 1.5))

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
            img.paste(logo, (25, 20), logo if logo.mode == "RGBA" else None)
            x_offset = 90
        except Exception:
            pass

    draw.text(
        (x_offset, 22),
        "ORÇAMENTO IMPRESSÃO 3D",
        fill=(255, 255, 255),
        font=fonte_titulo,
    )
    nome_cli = cliente.strip() if cliente and cliente.strip() else "Não informado"
    draw.text((x_offset, 50), f"Cliente: {nome_cli}", fill=(0, 180, 255), font=fonte_sub)

    tel_cli = telefone.strip() if telefone and telefone.strip() else "Não informado"
    draw.text((x_offset, 72), f"Telefone: {tel_cli}", fill=(180, 220, 255), font=fonte_texto)

    end_cli = endereco.strip() if endereco and endereco.strip() else "Não informado"
    draw.text((x_offset, 92), "Endereço:", fill=(160, 170, 190), font=fonte_texto)
    y_end = 112
    largura_max = 300
    palavras = end_cli.split()
    linha_atual = ""
    for palavra in palavras:
        teste = f"{linha_atual} {palavra}".strip()
        if draw.textlength(teste, font=fonte_texto) < largura_max:
            linha_atual = teste
        else:
            draw.text((x_offset, y_end), linha_atual, fill=(200, 200, 200), font=fonte_texto)
            y_end += 18
            linha_atual = palavra
            if y_end > 160:
                linha_atual = "..."
                break
    if linha_atual:
        draw.text((x_offset, y_end), linha_atual, fill=(200, 200, 200), font=fonte_texto)

    draw.line([(25, 175), (largura - 25, 175)], fill=(60, 70, 90), width=2)

    y = 190
    draw.text((25, y), "ITENS DO PEDIDO:", fill=(160, 170, 190), font=fonte_bold)
    y += 28

    for item in carrinho:
        mat = item.get("material_nome", "").strip()
        nome_peca = item["nome"]

        if len(nome_peca) > 35:
            nome_peca = nome_peca[:32] + "..."

        img_peca = carregar_imagem_peca(item.get("imagem"))
        x_texto = 25

        if img_peca:
            img_peca.thumbnail((45, 45))
            img.paste(img_peca, (25, y), img_peca if img_peca.mode == "RGBA" else None)
            x_texto = 80

        draw.text((x_texto, y), nome_peca, fill=(255, 255, 255), font=fonte_bold)
        y_item = y + 18

        if mat:
            draw.text((x_texto, y_item), f"[{mat}]", fill=(170, 180, 200), font=fonte_texto)
            y_item += 18

        detalhes = f"R$ {item['valor']:.2f}  |  {item['peso']:.0f}g  |  {item['tempo']:.1f}h"
        draw.text((x_texto, y_item), detalhes, fill=(130, 140, 160), font=fonte_texto)

        y += 70 if img_peca else 55

    draw.line([(25, y), (largura - 25, y)], fill=(60, 70, 90), width=1)
    y += 15

    draw.text((25, y), f"Totais: {subtotal_peso:.0f}g  |  {subtotal_tempo:.1f}h de máquina",
              fill=(170, 180, 200), font=fonte_texto)
    y += 26

    draw.text((25, y), f"VALOR TOTAL: R$ {total_final:.2f}",
              fill=(80, 220, 100), font=fonte_destaque)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def render_carrinho(conn, cursor):
    """Página pública do carrinho — mostra só o que o cliente adicionou
    e permite finalizar o pedido com Nome, Telefone e Endereço.
    Sem campo de ajuste de valor (isso é interno, não do cliente)."""
    st.title("🛒 Seu Carrinho")

    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    if st.button("← Continuar Comprando", use_container_width=False, key="carrinho_continuar_comprando"):
        st.session_state.pagina_atual = "Catalogo de Pecas"
        st.rerun()

    if not st.session_state.carrinho:
        st.info("Seu carrinho está vazio. Adicione peças pelo Catálogo.")
        return

    subtotal_peso = sum(item.get("peso", 0.0) for item in st.session_state.carrinho)
    subtotal_tempo = sum(item.get("tempo", 0.0) for item in st.session_state.carrinho)
    subtotal_valor = sum(item.get("valor", 0.0) for item in st.session_state.carrinho)

    st.subheader("Itens no Carrinho")
    for idx, item in enumerate(st.session_state.carrinho):
        with st.container(border=True):
            c_img, c_i1, c_i2 = st.columns([1, 3, 0.8])

            with c_img:
                if item.get("imagem"):
                    st.image(item["imagem"], width=60)
                else:
                    st.caption("🖼️ Sem foto")

            with c_i1:
                st.write(f"**{item.get('nome', 'Item')}**")
                st.caption(
                    f"Tempo: {item.get('tempo', 0.0):.1f}h | Valor: **R$ {item.get('valor', 0.0):.2f}**"
                )

            with c_i2:
                if st.button("❌", key=f"remover_item_{idx}"):
                    st.session_state.carrinho.pop(idx)
                    st.rerun()

    st.divider()

    total_final_pedido = subtotal_valor

    st.metric(
        "Total Final do Pedido",
        f"R$ {total_final_pedido:.2f}",
        delta=f"{subtotal_peso:.0f}g | {subtotal_tempo:.1f}h total",
    )

    st.subheader("Seus Dados")
    cursor.execute("SELECT nome FROM clientes ORDER BY nome ASC")
    clientes_cadastrados = [c[0] for c in cursor.fetchall()]

    if clientes_cadastrados:
        opcoes_cliente = ["-- Digitar Nome Manualmente --"] + clientes_cadastrados
        cli_selecionado = st.selectbox("Selecione o Cliente:*", opcoes_cliente)

        if cli_selecionado == "-- Digitar Nome Manualmente --":
            cliente_final = st.text_input("Nome do Cliente*", value="", placeholder="Digite seu nome completo")
        else:
            cliente_final = cli_selecionado
    else:
        cliente_final = st.text_input("Nome do Cliente*", value="", placeholder="Digite seu nome completo")

    telefone_final = st.text_input("WhatsApp / Telefone*", value="", placeholder="(XX) XXXXX-XXXX")
    endereco_final = st.text_area("Endereço para Entrega*", value="",
                                   placeholder="Rua, Número, Bairro, Cidade/UF, CEP")

    st.write("---")

    if st.button("🖼️ Gerar/Atualizar Imagem do Orçamento", use_container_width=True, key="carrinho_gerar_imagem"):
        if not cliente_final.strip():
            st.warning("⚠️ Digite o Nome do Cliente antes de gerar o orçamento.")
        else:
            buf_img = gerar_imagem_orcamento(
                cliente_final.strip(),
                telefone_final.strip(),
                endereco_final.strip(),
                st.session_state.carrinho,
                subtotal_peso,
                subtotal_tempo,
                total_final_pedido,
            )
            st.session_state["buf_orcamento"] = buf_img.getvalue()

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
        key="carrinho_finalizar_pedido",
    ):
        nome_ok = bool(cliente_final.strip())
        tel_ok = bool(telefone_final.strip())
        end_ok = bool(endereco_final.strip())

        if not nome_ok:
            st.error("⚠️ Informe o **Nome do Cliente**.")
        elif not tel_ok:
            st.error("⚠️ Informe o **Telefone / WhatsApp**.")
        elif not end_ok:
            st.error("⚠️ Informe o **Endereço de Entrega**.")
        else:
            resumo_pecas = " + ".join([
                item["nome"] for item in st.session_state.carrinho
            ])

            primeiro_material_id = st.session_state.carrinho[0]["material_id"]

            cursor.execute(
                """
                INSERT INTO pedidos (
                    cliente, telefone, endereco, nome_peca, material_id,
                    peso_g, tempo_h, valor_total, status, data_criado
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    cliente_final.strip(),
                    telefone_final.strip(),
                    endereco_final.strip(),
                    resumo_pecas,
                    primeiro_material_id,
                    subtotal_peso,
                    subtotal_tempo,
                    total_final_pedido,
                    "Pendente",
                ),
            )
            conn.commit()

            st.session_state.carrinho = []
            if "buf_orcamento" in st.session_state:
                del st.session_state["buf_orcamento"]

            st.success("✅ Pedido criado com sucesso! Obrigado pela preferência!")
            st.rerun()
