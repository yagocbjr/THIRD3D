import base64
import io
import json
import sqlite3
import time
import hashlib
from datetime import datetime
import os
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

# ✅ PRIMEIRA LINHA SEMPRE — REGRA OBRIGATÓRIA DO STREAMLIT!
st.set_page_config(
    page_title="ERP 3D THIRD", page_icon="logo.png", layout="wide"
)

from paginas.faturamento import render_faturamento
from paginas.calculadora import render_calculadora
from paginas.carrinho import render_carrinho
from paginas.catalogo import render_catalogo
from paginas.catalogo_admin import render_catalogo_admin
from paginas.clientes import render_clientes
from paginas.dashboard import render_dashboard
from paginas.encomendas import render_encomendas
from paginas.estoque import render_estoque
from paginas.pedidos import render_pedidos
from paginas.quadroideias import render_quadro_ideias

# ✅ IMPRESSORAS REMOVIDA — conforme solicitado

# ✅ ESCONDE A BARRA
st.markdown("""
<style>
[data-testid="stToolbar"] { display: none !important; }
header { visibility: hidden !important; height: 0 !important; }
.stApp { padding-top: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ========== SISTEMA DE LOGIN ==========
def verificar_senha(senha_digitada, senha_hash):
    return hashlib.sha256(senha_digitada.encode()).hexdigest() == senha_hash

senha_escolhida = "123"
senha_gerada = hashlib.sha256(senha_escolhida.encode()).hexdigest()

USUARIOS = {
    "yago": {
        "nome": "Teles",
        "senha_hash": senha_gerada
    }
}

def tela_login():
    st.markdown("""
    <style>
    .login-box {
        background: rgba(35, 35, 45, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        padding: 2.5rem;
        max-width: 400px;
        margin: 4rem auto;
        backdrop-filter: blur(16px);
        text-align: center;
    }
    .login-box h2 { margin-bottom: 1.5rem; color: white; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("<h2>Acesso ao ERP 3D</h2>", unsafe_allow_html=True)

    usuario = st.text_input("Usuário", placeholder="Digite seu usuário", key="login_usuario")
    senha = st.text_input("Senha", type="password", placeholder="Digite sua senha", key="login_senha")

    if st.button("Entrar", use_container_width=True, key="btn_entrar"):
        if usuario in USUARIOS:
            if verificar_senha(senha, USUARIOS[usuario]["senha_hash"]):
                st.session_state.logado = True
                st.session_state.usuario = USUARIOS[usuario]["nome"]
                st.rerun()
            else:
                st.error("Senha incorreta!")
        else:
            st.error("Usuário não encontrado!")

    st.markdown("</div>", unsafe_allow_html=True)


# --- BACKUP MANUAL ---
def fazer_backup():
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"backup_erp_3d_{data_hora}.db"
    caminho_banco = "erp_3d.db"

    if not os.path.exists(caminho_banco):
        return None, "Banco de dados não encontrado"

    with open(caminho_banco, "rb") as f:
        dados = f.read()
    return nome_arquivo, dados


def converter_imagem_base64(uploaded_file, largura_max=300, qualidade=80):
    if uploaded_file is None:
        return None
    try:
        img = Image.open(uploaded_file)
        img = img.convert("RGB")
        w, h = img.size
        if w > largura_max:
            proporcao = largura_max / w
            nova_largura = largura_max
            nova_altura = int(h * proporcao)
            img = img.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=qualidade, optimize=True)
        base64_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/jpeg;base64,{base64_str}"
    except Exception as e:
        st.error(f"Erro ao processar imagem: {str(e)}")
        return None


css_estilo = """
<style>
.stApp {
    background: linear-gradient(135deg, #4A4A4A 0%, #2B2B2B 50%, #121212 100%);
    background-attachment: fixed;
    background-size: cover;
}
section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(24px) saturate(180%);
    border-right: 1px solid rgba(255, 255, 255, 0.12);
    width: 220px;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    margin: 6px 0;
    font-size: 16px;
}
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


# --- LOGOTIPO E BOAS-VINDAS ---
st.sidebar.image("logo.png", use_container_width=True)
st.sidebar.title("3DThird.D")
if st.session_state.get("logado"):
    st.sidebar.markdown(f"Bem-vindo, {st.session_state.usuario}!")
st.sidebar.divider()


# --- BOTÃO DE BACKUP ---
if st.session_state.get("logado"):
    if st.sidebar.button("Baixar Backup", use_container_width=True, key="btn_backup"):
        nome_arq, dados = fazer_backup()
        if nome_arq and dados:
            st.sidebar.success("Pronto! Baixando...")
            st.download_button(
                label="Clique aqui para salvar",
                data=dados,
                file_name=nome_arq,
                mime="application/octet-stream",
                key="download_backup"
            )
        else:
            st.sidebar.error(f"Erro: {dados}")


# --- BANCO DE DADOS — Inicialização segura ---
@st.cache_resource
def conectar_banco():
    conn = sqlite3.connect("erp_3d.db", check_same_thread=False)
    return conn

conn = conectar_banco()
cursor = conn.cursor()

def inicializar_banco():
    try:
        cursor.execute("ALTER TABLE pecas_padrao ADD COLUMN imagem TEXT")
        conn.commit()
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE pecas_padrao ADD COLUMN custo_adicional REAL DEFAULT 0.0")
        conn.commit()
    except Exception: pass
    try:
        cursor.execute("ALTER TABLE pedidos ADD COLUMN data_criado DATETIME DEFAULT CURRENT_TIMESTAMP")
        conn.commit()
    except Exception: pass

    try: cursor.execute("ALTER TABLE materiais ADD COLUMN marca_id INTEGER")
    except sqlite3.OperationalError: pass
    try: cursor.execute("ALTER TABLE materiais ADD COLUMN cor TEXT DEFAULT ''")
    except sqlite3.OperationalError: pass

    # ✅ TABELA DE IDEIAS PERSONALIZADAS — CRIADA AQUI
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ideias_personalizadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_nome TEXT NOT NULL,
        telefone TEXT,
        descricao TEXT NOT NULL,
        referencia_link TEXT,
        imagem BLOB,
        prioridade TEXT DEFAULT 'Média',
        status TEXT DEFAULT '🟡 Procurando STL',
        observacoes TEXT,
        data_registro DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL, telefone TEXT, observacoes TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS marcas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materiais (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT DEFAULT '',
        marca_id INTEGER, cor TEXT DEFAULT '', tipo TEXT NOT NULL,
        preco_kg REAL NOT NULL, quantidade_g REAL NOT NULL,
        FOREIGN KEY (marca_id) REFERENCES marcas (id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT NOT NULL,
        nome_peca TEXT NOT NULL, material_id INTEGER, peso_g REAL NOT NULL,
        tempo_h REAL NOT NULL, valor_total REAL NOT NULL, status TEXT NOT NULL,
        estoque_baixado INTEGER DEFAULT 0,
        data_criado DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (material_id) REFERENCES materiais (id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pecas_padrao (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome_peca TEXT NOT NULL,
        material_id INTEGER, peso_g REAL NOT NULL, tempo_h REAL NOT NULL,
        preco_sugerido REAL NOT NULL, custo_producao REAL DEFAULT 0.0,
        FOREIGN KEY (material_id) REFERENCES materiais (id)
    )""")
    conn.commit()

inicializar_banco()


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

# ✅ IMPRESSORIAS REMOVIDA DA LISTA
PAGINAS_ADMIN = {"Dashboard", "Faturamento", "Clientes", "Estoque de Filamentos", "Fila de Pedidos", "Gerenciar Catalogo", "Calculadora"}
aba = st.session_state.get("pagina_atual", "Catalogo de Pecas")

estilo_menu = """
<style>
div.stButton > button {
    width: 100%; text-align: left; padding: 12px 16px;
    font-size: 15px; font-weight: 500; border-radius: 10px;
    border: none; margin: 4px 0;
}
div.stButton > button:hover {
    background-color: rgba(255,255,255,0.2);
}
</style>
"""
st.sidebar.markdown(estilo_menu, unsafe_allow_html=True)

# --- PÁGINAS PÚBLICAS ---
if st.sidebar.button("Catalogo de Pecas", use_container_width=True, key="menu_catalogo"):
    aba = "Catalogo de Pecas"
    st.session_state.pagina_atual = aba
if st.sidebar.button("Ideias Personalizadas", use_container_width=True, key="menu_encomendas"):
    aba = "Ideias Personalizadas"
    st.session_state.pagina_atual = aba
if st.sidebar.button("Carrinho", use_container_width=True, key="menu_carrinho"):
    aba = "Carrinho"
    st.session_state.pagina_atual = aba

st.sidebar.divider()

# --- ÁREA ADMINISTRATIVA ---
if st.session_state.get("logado"):
    if st.sidebar.button("Dashboard", use_container_width=True, key="menu_dashboard"):
        aba = "Dashboard"
        st.session_state.pagina_atual = aba
    if st.sidebar.button("Faturamento", use_container_width=True, key="menu_faturamento"):
        aba = "Faturamento"
        st.session_state.pagina_atual = aba
    # ✅ BOTÃO IMPRESSORIAS REMOVIDO
    if st.sidebar.button("Clientes", use_container_width=True, key="menu_clientes"):
        aba = "Clientes"
        st.session_state.pagina_atual = aba
    if st.sidebar.button("Estoque de Filamentos", use_container_width=True, key="menu_estoque"):
        aba = "Estoque de Filamentos"
        st.session_state.pagina_atual = aba
    if st.sidebar.button("Gerenciar Catalogo", use_container_width=True, key="menu_catalogo_admin"):
        aba = "Gerenciar Catalogo"
        st.session_state.pagina_atual = aba
    if st.sidebar.button("Calculadora", use_container_width=True, key="menu_calculadora"):
        aba = "Calculadora"
        st.session_state.pagina_atual = aba
    if st.sidebar.button("Fila de Pedidos", use_container_width=True, key="menu_pedidos"):
        aba = "Fila de Pedidos"
        st.session_state.pagina_atual = aba
    if st.sidebar.button("📋 Quadro de Ideias", use_container_width=True, key="menu_quadro"):
        aba = "QuadroIdeias"
        st.session_state.pagina_atual = aba
    if st.sidebar.button("Sair da Área Admin", use_container_width=True, key="menu_sair"):
        st.session_state.logado = False
        st.session_state.pagina_atual = "Catalogo de Pecas"
        st.rerun()
else:
    if st.sidebar.button("🔒 Área Administrativa", use_container_width=True, key="menu_login"):
        aba = "Login Admin"
        st.session_state.pagina_atual = aba

st.sidebar.divider()


# --- ROTEAMENTO DE PÁGINAS ---
if aba == "Login Admin":
    tela_login()
elif aba in PAGINAS_ADMIN and not st.session_state.get("logado"):
    st.warning("🔒 Essa área é restrita. Faça login para continuar.")
    tela_login()
elif aba == "Dashboard":
    render_dashboard(conn, cursor)
elif aba == "Faturamento":
    render_faturamento(conn, cursor)
elif aba == "Ideias Personalizadas":
    render_encomendas(conn, cursor)
# ✅ IMPRESSORIAS REMOVIDA DO ROTEAMENTO
elif aba == "Clientes":
    render_clientes(conn, cursor)
elif aba == "Estoque de Filamentos":
    render_estoque(conn, cursor, formatar_nome_material)
elif aba == "Calculadora":
    render_calculadora(conn, cursor)
elif aba == "Carrinho":
    render_carrinho(conn, cursor)
elif aba == "Catalogo de Pecas":
    render_catalogo(conn, cursor)
elif aba == "Gerenciar Catalogo":
    render_catalogo_admin(conn, cursor, converter_imagem_base64)
elif aba == "Fila de Pedidos":
    render_pedidos(conn, cursor, formatar_nome_material)
elif aba == "QuadroIdeias":
    render_quadro_ideias(conn, cursor)
