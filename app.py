import base64
import io
import json
import sqlite3
import ssl
import time
import shutil
from datetime import datetime
import os
import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from paginas.faturamento import render_faturamento
# Importação de todas as páginas
from paginas.calculadora import render_calculadora
from paginas.catalogo import render_catalogo
from paginas.clientes import render_clientes
from paginas.dashboard import render_dashboard
from paginas.encomendas import render_encomendas
from paginas.estoque import render_estoque
from paginas.impressoras import render_impressoras
from paginas.pedidos import render_pedidos


# --- 💾 FUNÇÃO DE BACKUP — ADAPTADA PRA NUVEM ---
def fazer_backup():
    """Baixa o banco de dados com data e hora no nome"""
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"backup_erp_3d_{data_hora}.db"
    caminho_banco = "erp_3d.db"  # Mesmo nome do seu banco
    
    if not os.path.exists(caminho_banco):
        return None, "Banco de dados não encontrado"
    
    # Lê o arquivo para download
    with open(caminho_banco, "rb") as f:
        dados = f.read()
    
    return nome_arquivo, dados


def converter_imagem_base64(uploaded_file, largura_max=300, qualidade=80):
    """✅ Versão INFALÍVEL — converte SEMPRE para RGB antes de tudo!"""
    if uploaded_file is None:
        return None

    try:
        # Abre a imagem
        img = Image.open(uploaded_file)
        
        # ✅ FORÇA CONVERSÃO PARA RGB — NÃO IMPORTA O FORMATO ORIGINAL!
        img = img.convert("RGB")
        
        # Redimensiona mantendo proporção
        w, h = img.size
        if w > largura_max:
            proporcao = largura_max / w
            nova_largura = largura_max
            nova_altura = int(h * proporcao)
            img = img.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)
        
        # Salva como JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=qualidade, optimize=True)
        base64_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/jpeg;base64,{base64_str}"
    except Exception as e:
        st.error(f"Erro ao processar imagem: {str(e)}")
        return None

# 1. Configuração da página e ícone no navegador
st.set_page_config(
    page_title="ERP 3D THIRD", page_icon="logo.png", layout="wide"
)

css_estilo = """
<style>
/* ===== FUNDO GRADIENTE: CINZA PARA PRETO ===== */
.stApp {
    background: linear-gradient(135deg, #4A4A4A 0%, #2B2B2B 50%, #121212 100%);
    background-attachment: fixed;
    background-size: cover;
}

/* ===== MENU LATERAL VIDRO ===== */
section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(24px) saturate(180%);
    border-right: 1px solid rgba(255, 255, 255, 0.12);
    width: 220px;
}

/* ===== LOGO MENOR ===== */
section[data-testid="stSidebar"] div[data-testid="stImage"] {
    max-width: 140px;
    margin: 0 auto 10px auto;
}

/* ===== TÍTULOS MENOS ESPAÇO ===== */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    margin: 6px 0;
    font-size: 16px;
}

/* ===== BOTÕES COMPACTOS ===== */
div.stButton > button {
    width: 100%;
    text-align: left;
    padding: 8px 12px;
    font-size: 13px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.10);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.18);
    color: #FFFFFF;
    margin: 3px 0;
    min-height: 40px;
}
div.stButton > button:hover {
    background: rgba(255, 255, 255, 0.20);
    transform: translateY(-1px);
}

/* ===== REMOVER ESPAÇOS EXTRAS ===== */
section[data-testid="stSidebar"] div.stMarkdown {
    margin: 0;
    padding: 0;
}
section[data-testid="stSidebar"] hr {
    margin: 8px 0;
}

/* ===== FORMULÁRIOS E CAMPOS ===== */
div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 16px;
    padding: 20px;
}
div[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 16px;
}
div[data-testid="stTextInput"] > div > div > input,
div[data-testid="stTextArea"] > div > div > textarea,
div[data-testid="stNumberInput"] > div > div > input {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 10px;
    color: #FFFFFF;
}
div[data-testid="stDataFrame"] > div {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 16px;
}
div[data-testid="stDataFrame"] table th {
    background: rgba(255, 255, 255, 0.12);
    color: #FFFFFF;
}
div[data-testid="stDataFrame"] table td {
    color: #FFFFFF;
}
div[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 16px;
    padding: 16px;
}
div.stAlert {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 14px;
}
h1, h2, h3, h4, h5, h6, p, label, span {
    color: #FFFFFF;
}
</style>
"""

st.markdown(css_estilo, unsafe_allow_html=True)


# 2. Exibir o Logotipo no topo da barra lateral (Sidebar)
st.sidebar.image("logo.png", use_container_width=True)
st.sidebar.title("3DThird.D")

# --- BOTÃO DE BACKUP MANUAL na Sidebar ---
st.sidebar.divider()
if st.sidebar.button("💾 Baixar Backup", use_container_width=True):
    nome_arq, dados = fazer_backup()
    if nome_arq and dados:
        st.sidebar.success("✅ Pronto! Baixando...")
        st.download_button(
            label="📂 Clique aqui para salvar",
            data=dados,
            file_name=nome_arq,
            mime="application/octet-stream"
        )
    else:
        st.sidebar.error(f"❌ Erro: {dados}")

# --- BANCO DE DADOS ---
conn = sqlite3.connect("erp_3d.db", check_same_thread=False)
cursor = conn.cursor()

# Garante que a coluna 'imagem' existe na tabela 'pecas_padrao'
try:
    cursor.execute("ALTER TABLE pecas_padrao ADD COLUMN imagem TEXT")
    conn.commit()
except Exception:
    pass
# Garante que a coluna 'custo_adicional' existe na tabela 'pecas_padrao'
try:
    cursor.execute(
        "ALTER TABLE pecas_padrao ADD COLUMN custo_adicional REAL DEFAULT 0.0"
    )
    conn.commit()
except Exception:
    pass
try:
    cursor.execute(
        "ALTER TABLE pedidos ADD COLUMN data_criado DATETIME DEFAULT CURRENT_TIMESTAMP"
    )
    conn.commit()
except Exception:
    pass
try:
    cursor.execute("ALTER TABLE impressoras RENAME TO impressoras_old")
    cursor.execute("""
        CREATE TABLE impressoras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            ip TEXT,
            access_code TEXT,
            serial TEXT,
            modelo TEXT DEFAULT 'A1',
            token_nuvem TEXT
        )
    """)
    cursor.execute("""
        INSERT INTO impressoras (id, nome, ip, access_code, serial, modelo)
        SELECT id, nome, ip, access_code, serial, modelo FROM impressoras_old
    """)
    cursor.execute("DROP TABLE impressoras_old")
    conn.commit()
except Exception as e:
    pass


# Tabela de Clientes
cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    telefone TEXT,
    observacoes TEXT
)
""")

# Tabela de Marcas
cursor.execute("""
CREATE TABLE IF NOT EXISTS marcas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
)
""")

# Tabela de Materiais
cursor.execute("""
CREATE TABLE IF NOT EXISTS materiais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT DEFAULT '',
    marca_id INTEGER,
    cor TEXT DEFAULT '',
    tipo TEXT NOT NULL,
    preco_kg REAL NOT NULL,
    quantidade_g REAL NOT NULL,
    FOREIGN KEY (marca_id) REFERENCES marcas (id)
)
""")

try:
    cursor.execute("ALTER TABLE materiais ADD COLUMN marca_id INTEGER")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE materiais ADD COLUMN cor TEXT DEFAULT ''")
except sqlite3.OperationalError:
    pass

# Tabela de Pedidos
cursor.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    nome_peca TEXT NOT NULL,
    material_id INTEGER,
    peso_g REAL NOT NULL,
    tempo_h REAL NOT NULL,
    valor_total REAL NOT NULL,
    status TEXT NOT NULL,
    estoque_baixado INTEGER DEFAULT 0,
    data_criado DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES materiais (id)
)
""")

# Tabela de Impressoras
cursor.execute("""
CREATE TABLE IF NOT EXISTS impressoras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    ip TEXT NOT NULL,
    access_code TEXT NOT NULL,
    serial TEXT NOT NULL,
    modelo TEXT DEFAULT 'Bambu Lab A1'
)
""")

# Tabela de Peças Padrão
cursor.execute("""
CREATE TABLE IF NOT EXISTS pecas_padrao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_peca TEXT NOT NULL,
    material_id INTEGER,
    peso_g REAL NOT NULL,
    tempo_h REAL NOT NULL,
    preco_sugerido REAL NOT NULL,
    custo_producao REAL DEFAULT 0.0,
    FOREIGN KEY (material_id) REFERENCES materiais (id)
)
""")
conn.commit()

# Inicialização do Carrinho
if "carrinho" not in st.session_state:
    st.session_state.carrinho = []


def formatar_nome_material(m_id, marca_nome, cor, tipo, nome_antigo=None):
    if marca_nome and cor:
        return f"{marca_nome} - {cor} ({tipo})"
    elif nome_antigo:
        return f"{nome_antigo} ({tipo})"
    else:
        return f"Material #{m_id} ({tipo})"


# --- NAVEGAÇÃO ---
st.sidebar.divider()
aba = st.session_state.get("pagina_atual", "📊 Dashboard")

estilo_menu = """
<style>
div.stButton > button {
    width: 100%;
    text-align: left;
    padding: 12px 16px;
    font-size: 15px;
    font-weight: 500;
    border-radius: 10px;
    border: none;
    margin: 4px 0;
}
div.stButton > button:hover {
    background-color: rgba(255,255,255,0.2);
}
</style>
"""
st.sidebar.markdown(estilo_menu, unsafe_allow_html=True)

# Botões com ícones
if st.sidebar.button("📊  Dashboard", use_container_width=True):
    aba = "📊 Dashboard"
    st.session_state.pagina_atual = aba
if st.sidebar.button("💰  Faturamento", use_container_width=True):
    aba = "💰 Faturamento"
    st.session_state.pagina_atual = aba
if st.sidebar.button("💡  Ideias Personalizadas", use_container_width=True):
    aba = "💡 Ideias Personalizadas"
    st.session_state.pagina_atual = aba
if st.sidebar.button("🖨️  Impressoras", use_container_width=True):
    aba = "🖨️ Impressoras"
    st.session_state.pagina_atual = aba
if st.sidebar.button("👤  Clientes", use_container_width=True):
    aba = "👤 Clientes"
    st.session_state.pagina_atual = aba
if st.sidebar.button("📦  Estoque de Filamentos", use_container_width=True):
    aba = "📦 Estoque de Filamentos"
    st.session_state.pagina_atual = aba
if st.sidebar.button("🛒  Calculadora & Carrinho", use_container_width=True):
    aba = "🛒 Calculadora & Carrinho"
    st.session_state.pagina_atual = aba
if st.sidebar.button("🧩  Catálogo de Peças", use_container_width=True):
    aba = "🧩 Catálogo de Peças"
    st.session_state.pagina_atual = aba
if st.sidebar.button("📋  Fila de Pedidos", use_container_width=True):
    aba = "📋 Fila de Pedidos"
    st.session_state.pagina_atual = aba

st.sidebar.divider()

# --- ROTEAMENTO DE ABAS ---
if aba == "📊 Dashboard":
    render_dashboard(conn, cursor)
elif aba == "💰 Faturamento":
    render_faturamento(conn, cursor)
elif aba == "💡 Ideias Personalizadas":
    render_encomendas(conn, cursor)
elif aba == "🖨️ Impressoras":
    render_impressoras(conn, cursor)
elif aba == "👤 Clientes":
    render_clientes(conn, cursor)
elif aba == "📦 Estoque de Filamentos":
    render_estoque(conn, cursor, formatar_nome_material)
elif aba == "🛒 Calculadora & Carrinho":
    render_calculadora(conn, cursor)
elif aba == "🧩 Catálogo de Peças":
    render_catalogo(conn, cursor, converter_imagem_base64)
elif aba == "📋 Fila de Pedidos":
    render_pedidos(conn, cursor, formatar_nome_material)