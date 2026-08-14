import streamlit as st
import json
import ssl
import time
import paho.mqtt.client as mqtt

def render_impressoras(conn, cursor):
    st.title("🖨️ Gestão & Monitoramento de Impressoras")
    st.caption("Cadastre e acompanhe o status em tempo real das suas Bambu Lab A1.")

    # 1. Formulário de Cadastro
    with st.expander("➕ Cadastrar Nova Impressora", expanded=False):
        with st.form("form_impressora", clear_on_submit=True):
            col_imp1, col_imp2 = st.columns(2)
            with col_imp1:
                nome_imp = st.text_input("Nome/Identificação*", placeholder="Ex: Bambu A1 #1")
                ip_imp = st.text_input("Endereço IP (Local)", placeholder="Deixe em branco se usar só Nuvem")
            with col_imp2:
                access_code_imp = st.text_input("Access Code (Senha)*", type="password")
                token_imp = st.text_input("Token de Acesso (Nuvem)", type="password")
                serial_imp = st.text_input("Número de Série (Serial)*", placeholder="Ex: 03900D613121082")

            if st.form_submit_button("💾 Salvar Impressora", use_container_width=True):
                if nome_imp and serial_imp:
                    try:
                        cursor.execute("""
                            INSERT INTO impressoras (nome, ip, access_code, serial, token_nuvem)
VALUES (?, ?, ?, ?, ?)
""", (nome_imp.strip(), ip_imp.strip() or None, access_code_imp.strip(), serial_imp.strip(), token_imp.strip() or None))
                        conn.commit()
                        st.success(f"Impressora '{nome_imp}' cadastrada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
                else:
                    st.warning("Preencha Nome, Access Code e Serial.")

    st.divider()

    # 2. Buscar impressoras do banco
    cursor.execute("SELECT id, nome, ip, access_code, serial, modelo, token_nuvem FROM impressoras ORDER BY id ASC")
    impressoras = cursor.fetchall()

    if impressoras:
        st.subheader("📡 Impressoras Cadastradas")

        cols_imp = st.columns(len(impressoras))
        for idx, imp in enumerate(impressoras):
            imp_id, imp_nome, imp_ip, imp_code, imp_serial, imp_modelo, imp_token = imp
            
            with cols_imp[idx]:
                st.write(f"### 🖨️ {imp_nome}")
                st.caption(f"IP: `{imp_ip or '---'}` | Serial: `{imp_serial}`")

                cache_key = f"status_imp_{imp_id}"
                if cache_key not in st.session_state:
                    st.session_state[cache_key] = {"conectado": False}

                col_btn, _ = st.columns([1, 0.1])
                with col_btn:
                    if st.button("🔄 Atualizar Status", key=f"btn_sync_{imp_id}", use_container_width=True):
                        st.session_state[cache_key] = buscar_status_bambu(imp_ip, imp_code, imp_serial, idx, imp_token)
                        st.rerun()

                status = st.session_state[cache_key]
                if not status.get("conectado"):
                    status = buscar_status_bambu(imp_ip, imp_code, imp_serial, idx)
                    st.session_state[cache_key] = status

                if status.get("conectado"):
                    st.success("🟢 ON-LINE")
                    prog = status.get('progresso', 0)
                    st.progress(prog / 100.0, text=f"Progresso: {prog}%")

                    c1_stat, c2_stat = st.columns(2)
                    c1_stat.metric("🌡️ Bico", f"{status.get('temp_bico', 0.0):.1f}°C")
                    c2_stat.metric("🛏️ Mesa", f"{status.get('temp_mesa', 0.0):.1f}°C")

                    tempo_min = status.get('tempo_restante', 0)
                    horas = tempo_min // 60
                    mins = tempo_min % 60
                    tempo_fmt = f"{horas}h {mins}min" if horas > 0 else f"{mins} min"

                    st.info(f"⏱️ Tempo restante: **{tempo_fmt}**\n\n📌 Estado: `{status.get('estado', 'UNKNOWN')}`")
                else:
                    st.error("🔴 OFF-LINE ou Sem Resposta\n\n*(Verifique Modo LAN e Wi-Fi)*")

                with st.popover("⚙️ Opções"):
                    if st.button("❌ Excluir Impressora", key=f"del_imp_{imp_id}", type="primary", use_container_width=True):
                        cursor.execute("DELETE FROM impressoras WHERE id = ?", (imp_id,))
                        conn.commit()
                        if cache_key in st.session_state:
                            del st.session_state[cache_key]
                        st.rerun()
    else:
        st.info("Nenhuma impressora cadastrada ainda. Utilize o formulário acima para salvar sua Bambu A1!")


def buscar_status_bambu(ip, access_code, serial, idx_cli, token_nuvem=None):
    """Conecta pela NUVEM Bambu Lab ou rede local."""
    res = {"conectado": False, "progresso": 0, "tempo_restante": 0, "temp_bico": 0.0, "temp_mesa": 0.0, "estado": "N/A"}

    def ler_mensagem(payload, res_dict):
        if "print" in payload:
            info = payload["print"]
            res_dict["conectado"] = True
            if "gcode_state" in info:
                res_dict["estado"] = info["gcode_state"]
            if "mc_percent" in info:
                res_dict["progresso"] = int(info["mc_percent"])
            if "mc_remaining_time" in info:
                res_dict["tempo_restante"] = int(info["mc_remaining_time"])
            if "nozzle_temper" in info:
                res_dict["temp_bico"] = float(info["nozzle_temper"])
            if "bed_temper" in info:
                res_dict["temp_mesa"] = float(info["bed_temper"])

    def conectar_mqtt(host, porta, usuario, senha, usar_ssl=True):
        dados_recebidos = {"conectado": False}

        def on_connect(client, userdata, flags, rc, properties=None):
            if rc == 0:
                client.subscribe(f"device/{serial}/report")
                payload_push = json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}})
                client.publish(f"device/{serial}/request", payload_push)

        def on_message(client, userdata, msg):
            try:
                ler_mensagem(json.loads(msg.payload.decode('utf-8')), dados_recebidos)
            except Exception:
                pass

        try:
            try:
                client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=f"ERP_{serial}_{idx_cli}_{int(time.time())}")
            except AttributeError:
                client = mqtt.Client(client_id=f"ERP_{serial}_{idx_cli}_{int(time.time())}")

            client.username_pw_set(usuario, senha)
            if usar_ssl:
                client.tls_set(cert_reqs=ssl.CERT_NONE)
                client.tls_insecure_set(True)
            client.on_connect = on_connect
            client.on_message = on_message

            client.connect(host, porta, timeout=5)
            client.loop_start()

            t_inicio = time.time()
            while time.time() - t_inicio < 6:
                if dados_recebidos["conectado"] and dados_recebidos.get("temp_bico", 0) > 0:
                    break
                time.sleep(0.1)

            client.loop_stop()
            client.disconnect()
        except Exception as e:
            pass
        return dados_recebidos

    # ==============================================
    # ☁️ CONEXÃO PELA NUVEM BAMBU
    # ==============================================
    if token_nuvem and serial:
        # ⚠️ NA NUVEM: Usuário = Serial, Senha = Token
        res_nuvem = conectar_mqtt(
            "mqtt.bambulab.com", 8883,
            serial,           # ← Usuário = Serial da impressora
            token_nuvem,      # ← Senha = Token de Acesso
            usar_ssl=True
        )
        if res_nuvem["conectado"]:
            return res_nuvem

    # Fallback — tenta rede local
    if ip and access_code:
        res_local = conectar_mqtt(ip, 8883, "bblp", access_code, usar_ssl=True)
        if res_local["conectado"]:
            return res_local

    return res