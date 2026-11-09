import streamlit as st
import requests
import pandas as pd
import io
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Quantitativo de Painéis por inversor", layout="wide")

# --- GERENCIAMENTO DE CACHE ---
@st.cache_data(ttl=300)
def carregar_paineis_cached(api_url, apenas_disponiveis=False, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"apenas_disponiveis": str(apenas_disponiveis).lower()}
    try:
        res = requests.get(f"{api_url}/paineis/", params=params, headers=headers)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

@st.cache_data(ttl=300)
def carregar_inversores_cached(api_url, apenas_disponiveis=False, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"apenas_disponiveis": str(apenas_disponiveis).lower()}
    try:
        res = requests.get(f"{api_url}/inversores/", params=params, headers=headers)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

# SESSÃO
if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.role = "user"
    st.session_state.username = "Visitante"

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}

# --- BARRA LATERAL ---
st.sidebar.title("☀️ Dimensionador Solar")

if st.session_state.token and st.session_state.role == "admin":
    st.sidebar.success(f"🔑 Logado como Admin: **{st.session_state.username}**")
    if st.sidebar.button("Sair do Modo Admin"):
        st.session_state.token = None
        st.session_state.role = "user"
        st.session_state.username = "Visitante"
        st.cache_data.clear()
        st.rerun()
else:
    with st.sidebar.expander("🔒 Área do Administrador"):
        with st.form("admin_login_form"):
            u = st.text_input("Usuário")
            p = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                res = requests.post(f"{API_URL}/auth/login", data={"username": u, "password": p})
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.role = data["role"]
                    st.session_state.username = u
                    st.cache_data.clear()
                    st.success("Login efetuado!")
                    st.rerun()
                else:
                    st.error("Credenciais inválidas.")

menu = ["Calculadora MPPT"]
if st.session_state.role == "admin":
    menu.extend([
        "Gerenciar Disponibilidade (Loja)", 
        "Gestão de Painéis (CRUD)", 
        "Gestão de Inversores (CRUD)"
    ])

opcao = st.sidebar.radio("Navegação", menu)

# -------------------------------------------------------------
# 1. CALCULADORA MPPT
# -------------------------------------------------------------
if opcao == "Calculadora MPPT":
    st.title("Quantitativo de Painéis por Inversor - Sou Energy")

    st.sidebar.header("Parâmetros Globais")
    t_min = st.sidebar.number_input("T. Mínima Ambiente (°C)", value=0, step=1)
    t_max = st.sidebar.number_input("T. Máxima Painel (°C)", value=75, step=1)

    paineis = carregar_paineis_cached(API_URL, apenas_disponiveis=True)
    inversores = carregar_inversores_cached(API_URL, apenas_disponiveis=True)

    st.sidebar.header("Seleção de Equipamentos")
    opts_p = {f"[{p['sku']}] {p['fabricante']} {p['modelo']}": p['id'] for p in paineis}
    opts_i = {f"[{i['sku']}] {i['fabricante']} {i['modelo']}": i['id'] for i in inversores}

    sel_p = st.sidebar.multiselect("Filtrar Painel(is) em Loja:", options=["Todos"] + list(opts_p.keys()), default=["Todos"])
    sel_i = st.sidebar.multiselect("Filtrar Inversor(es) em Loja:", options=["Todos"] + list(opts_i.keys()), default=["Todos"])

    if st.button("Processar Quantitativo", type="primary"):
        ids_p = None if "Todos" in sel_p else [opts_p[k] for k in sel_p]
        ids_i = None if "Todos" in sel_i else [opts_i[k] for k in sel_i]

        payload = {
            "temp_min": float(t_min),
            "temp_max": float(t_max),
            "painel_ids": ids_p,
            "inversor_ids": ids_i
        }
        res = requests.post(f"{API_URL}/dimensionar/", json=payload)
        if res.status_code == 200:
            data = res.json()
            if not data:
                st.warning("Nenhuma combinação encontrada para os filtros aplicados.")
            else:
                df_res = pd.DataFrame(data)
                st.success(f"Concluído! {len(df_res)} combinação(ões) gerada(s).")
                st.dataframe(df_res, use_container_width=True)

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_res.to_excel(writer, index=False, sheet_name='Quantitativo_Estoque')

                st.download_button(
                    label="📥 Baixar Relatório (Excel)",
                    data=buffer.getvalue(),
                    file_name=f"Quantitativo_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# -------------------------------------------------------------
# 2. GERENCIAR DISPONIBILIDADE (LOJA)
# -------------------------------------------------------------
elif opcao == "Gerenciar Disponibilidade (Loja)":
    st.header("🛒 Gerenciar Disponibilidade de Equipamentos em Loja")
    st.caption("Marque ou desmarque os itens para controlar a visibilidade deles na Calculadora MPPT.")

    tab_p, tab_i = st.tabs(["Painéis Fotovoltaicos", "Inversores Solar"])

    with tab_p:
        paineis_all = carregar_paineis_cached(API_URL, apenas_disponiveis=False, token=st.session_state.token)
        if paineis_all:
            for p in paineis_all:
                c1, c2, c3 = st.columns([1, 4, 2])
                c1.write(f"**{p['sku']}**")
                c2.write(f"{p['fabricante']} {p['modelo']} ({p.get('potencia_wp', 0)}Wp)")
                disp = c3.checkbox("Disponível em Loja", value=p['disponivel'], key=f"disp_p_{p['id']}")
                if disp != p['disponivel']:
                    res = requests.patch(f"{API_URL}/paineis/{p['id']}/disponibilidade", params={"disponivel": str(disp).lower()}, headers=get_headers())
                    if res.status_code == 200:
                        st.cache_data.clear()
                        st.toast(f"Status do painel '{p['modelo']}' atualizado!", icon="✅")
                        st.rerun()

    with tab_i:
        inversores_all = carregar_inversores_cached(API_URL, apenas_disponiveis=False, token=st.session_state.token)
        if inversores_all:
            for i in inversores_all:
                c1, c2, c3 = st.columns([1, 4, 2])
                c1.write(f"**{i['sku']}**")
                c2.write(f"{i['fabricante']} {i['modelo']} ({i.get('pnom_kw', 0)}kW)")
                disp = c3.checkbox("Disponível em Loja", value=i['disponivel'], key=f"disp_i_{i['id']}")
                if disp != i['disponivel']:
                    res = requests.patch(f"{API_URL}/inversores/{i['id']}/disponibilidade", params={"disponivel": str(disp).lower()}, headers=get_headers())
                    if res.status_code == 200:
                        st.cache_data.clear()
                        st.toast(f"Status do inversor '{i['modelo']}' atualizado!", icon="✅")
                        st.rerun()

# -------------------------------------------------------------
# 3. GESTÃO COMPLETA DE PAINÉIS (CRUD)
# -------------------------------------------------------------
elif opcao == "Gestão de Painéis (CRUD)":
    st.header("⚡ Gestão de Painéis Fotovoltaicos")

    tab1, tab2 = st.tabs(["📋 Lista & Edição / Remoção", "➕ Cadastrar Novo Painel"])

    with tab1:
        search_p = st.text_input("🔍 Pesquisar por SKU, Fabricante ou Modelo:", "")
        paineis_list = carregar_paineis_cached(API_URL, apenas_disponiveis=False, token=st.session_state.token)

        if search_p:
            paineis_list = [
                p for p in paineis_list 
                if search_p.lower() in str(p.get('sku', '')).lower() 
                or search_p.lower() in str(p.get('fabricante', '')).lower() 
                or search_p.lower() in str(p.get('modelo', '')).lower()
            ]

        st.caption(f"Exibindo os primeiros {min(len(paineis_list), 30)} de {len(paineis_list)} painéis cadastrados. Use a busca acima para filtrar.")

        for p in paineis_list[:30]:
            pot_val = float(p.get('potencia_wp') or 0.0)
            with st.expander(f"[{p.get('sku', '-')}] {p.get('fabricante', '')} - {p.get('modelo', '')} ({pot_val}Wp)"):
                with st.form(f"edit_painel_{p['id']}"):
                    c1, c2, c3 = st.columns(3)
                    sku = c1.text_input("SKU", value=p.get('sku') or "-")
                    fab = c2.text_input("Fabricante", value=p.get('fabricante') or "")
                    mod = c3.text_input("Modelo", value=p.get('modelo') or "")

                    c4, c5, c6 = st.columns(3)
                    pot = c4.number_input("Potência (Wp)", value=float(p.get('potencia_wp') or 0.0))
                    voc = c5.number_input("Voc (V)", value=float(p.get('voc_v') or 0.0))
                    vmp = c6.number_input("Vmp (V)", value=float(p.get('vmp_v') or 0.0))

                    c7, c8, c9 = st.columns(3)
                    isc = c7.number_input("Isc (A)", value=float(p.get('isc_a') or 0.0))
                    imp = c8.number_input("Imp (A)", value=float(p.get('imp_a') or 0.0))
                    coef = c9.number_input("Coef. Temp Voc (%/°C)", value=float(p.get('coef_temp_voc') or -0.28))
                    disp = st.checkbox("Disponível em Loja", value=bool(p.get('disponivel', True)))

                    col_btn1, col_btn2 = st.columns([1, 1])
                    if col_btn1.form_submit_button("💾 Salvar Alterações"):
                        payload = {
                            "sku": sku, "fabricante": fab, "modelo": mod,
                            "potencia_wp": pot, "voc_v": voc, "vmp_v": vmp,
                            "isc_a": isc, "imp_a": imp, "coef_temp_voc": coef, "disponivel": disp
                        }
                        res = requests.put(f"{API_URL}/paineis/{p['id']}", json=payload, headers=get_headers())
                        if res.status_code == 200:
                            st.cache_data.clear()
                            st.success("Painel atualizado!")
                            st.rerun()

                if st.button(f"🗑️ Excluir Painel", key=f"del_p_{p['id']}", type="secondary"):
                    res = requests.delete(f"{API_URL}/paineis/{p['id']}", headers=get_headers())
                    if res.status_code in [200, 204]:
                        st.cache_data.clear()
                        st.toast("Painel removido!", icon="🗑️")
                        st.rerun()

    with tab2:
        with st.form("cad_painel_new", clear_on_submit=True):
            sku = st.text_input("SKU Painel", placeholder="Ex: P001")
            fab = st.text_input("Fabricante", placeholder="Ex: Canadian Solar")
            mod = st.text_input("Modelo", placeholder="Ex: CS6W-550MS")
            pot = st.number_input("Potência (Wp)", value=None, placeholder="Ex: 550")
            voc = st.number_input("Voc (V)", value=None, placeholder="Ex: 49.6")
            vmp = st.number_input("Vmp (V)", value=None, placeholder="Ex: 41.7")
            isc = st.number_input("Isc (A)", value=None, placeholder="Ex: 14.0")
            imp = st.number_input("Imp (A)", value=None, placeholder="Ex: 13.2")
            coef = st.number_input("Coef. Temp Voc (%/°C)", value=-0.28)
            disp_inicial = st.checkbox("Disponível em Loja Já no Cadastro?", value=True)

            if st.form_submit_button("Salvar Novo Painel"):
                if not all([sku, fab, mod, pot, voc, vmp, isc]):
                    st.error("Preencha os campos obrigatórios!")
                else:
                    data = {
                        "sku": sku, "fabricante": fab, "modelo": mod,
                        "potencia_wp": pot, "voc_v": voc, "vmp_v": vmp,
                        "isc_a": isc, "imp_a": imp or 0.0, "coef_temp_voc": coef, "disponivel": disp_inicial
                    }
                    res = requests.post(f"{API_URL}/paineis/", json=data, headers=get_headers())
                    if res.status_code == 201:
                        st.cache_data.clear()
                        st.success("Painel cadastrado com sucesso!")
                        st.rerun()

# -------------------------------------------------------------
# 4. GESTÃO COMPLETA DE INVERSORES (CRUD - ALTA PERFORMANCE)
# -------------------------------------------------------------
elif opcao == "Gestão de Inversores (CRUD)":
    st.header("🔌 Gestão de Inversores Solar")

    tab1, tab2 = st.tabs(["📋 Lista & Edição / Remoção", "➕ Cadastrar Novo Inversor"])

    with tab1:
        search_i = st.text_input("🔍 Pesquisar por SKU, Fabricante ou Modelo:", "")
        inversores_list = carregar_inversores_cached(API_URL, apenas_disponiveis=False, token=st.session_state.token)

        if search_i:
            inversores_list = [
                inv for inv in inversores_list 
                if search_i.lower() in str(inv.get('sku', '')).lower() 
                or search_i.lower() in str(inv.get('fabricante', '')).lower() 
                or search_i.lower() in str(inv.get('modelo', '')).lower()
            ]

        st.caption(f"Exibindo os primeiros {min(len(inversores_list), 20)} de {len(inversores_list)} inversores. Digite no campo acima para pesquisar qualquer item.")

        # Exibe apenas 20 por página para garantir rendering ultrarrápido
        for inv in inversores_list[:20]:
            pnom_val = float(inv.get('pnom_kw') or 0.0)
            with st.expander(f"[{inv.get('sku', '-')}] {inv.get('fabricante', '')} - {inv.get('modelo', '')} ({pnom_val}kW)"):
                with st.form(f"edit_inv_{inv['id']}"):
                    c1, c2, c3 = st.columns(3)
                    sku = c1.text_input("SKU", value=inv.get('sku') or "-")
                    fab = c2.text_input("Fabricante", value=inv.get('fabricante') or "")
                    mod = c3.text_input("Modelo", value=inv.get('modelo') or "")

                    c4, c5, c6, c7 = st.columns(4)
                    pnom = c4.number_input("Pnom (kW)", value=float(inv.get('pnom_kw') or 0.0))
                    pmax = c5.number_input("Pmax (W)", value=float(inv.get('pmax_w') or 0.0))
                    vmax = c6.number_input("Vmax (V)", value=float(inv.get('vmax_v') or 0.0))
                    vmin = c7.number_input("Vmin MPPT (V)", value=float(inv.get('vmin_v') or 0.0))

                    disp = st.checkbox("Disponível em Loja", value=bool(inv.get('disponivel', True)))

                    st.markdown("**Especificações das MPPTs**")
                    mppts_edit = []
                    for m in sorted(inv.get('mppts', []), key=lambda x: x.get('mppt_numero', 1)):
                        c_m1, c_m2, c_m3 = st.columns(3)
                        icc_m = c_m1.number_input(f"Icc MPPT {m['mppt_numero']} (A)", value=float(m.get('icc_a') or 0.0), key=f"icc_e_{inv['id']}_{m['mppt_numero']}")
                        imp_m = c_m2.number_input(f"Imp MPPT {m['mppt_numero']} (A)", value=float(m.get('imp_a') or 0.0), key=f"imp_e_{inv['id']}_{m['mppt_numero']}")
                        str_m = c_m3.number_input(f"Strings MPPT {m['mppt_numero']}", value=int(m.get('max_strings') or 1), step=1, key=f"str_e_{inv['id']}_{m['mppt_numero']}")
                        mppts_edit.append({"mppt_numero": m['mppt_numero'], "icc_a": icc_m, "imp_a": imp_m, "max_strings": int(str_m)})

                    if st.form_submit_button("💾 Salvar Alterações"):
                        payload = {
                            "sku": sku, "fabricante": fab, "modelo": mod,
                            "pnom_kw": pnom, "pmax_w": pmax, "vmax_v": vmax, "vmin_v": vmin,
                            "disponivel": disp, "mppts": mppts_edit
                        }
                        res = requests.put(f"{API_URL}/inversores/{inv['id']}", json=payload, headers=get_headers())
                        if res.status_code == 200:
                            st.cache_data.clear()
                            st.success("Inversor atualizado!")
                            st.rerun()

                if st.button(f"🗑️ Excluir Inversor", key=f"del_i_{inv['id']}", type="secondary"):
                    res = requests.delete(f"{API_URL}/inversores/{inv['id']}", headers=get_headers())
                    if res.status_code in [200, 204]:
                        st.cache_data.clear()
                        st.toast("Inversor removido!", icon="🗑️")
                        st.rerun()

    # ABA CADASTRO INSTANTÂNEO COM INPUT NUMÉRICO
    with tab2:
        qtd_mppts = st.number_input(
            "Quantidade de MPPTs do Inversor", 
            min_value=1, max_value=15, 
            value=2, step=1, 
            key="input_qtd_mppts"
        )

        with st.form("cad_inversor_new", clear_on_submit=True):
            sku = st.text_input("SKU Inversor", placeholder="Ex: INV001")
            fab = st.text_input("Fabricante", placeholder="Ex: Huawei")
            mod = st.text_input("Modelo", placeholder="Ex: SUN2000-10KTL-M1")
            pnom = st.number_input("Pnom (kW)", value=None, placeholder="Ex: 10.0")
            pmax = st.number_input("Pmax (W)", value=None, placeholder="Ex: 11000")
            vmax = st.number_input("Vmax (V)", value=None, placeholder="Ex: 11000")
            vmin = st.number_input("Vmin MPPT (V)", value=None, placeholder="Ex: 160")
            disp_inicial = st.checkbox("Disponível em Loja Já no Cadastro?", value=True)

            mppts_payload = []
            st.subheader("Especificações das MPPTs")
            for i in range(1, int(qtd_mppts) + 1):
                st.markdown(f"**MPPT {i}**")
                c1, c2, c3 = st.columns(3)
                icc = c1.number_input(f"Icc MPPT {i} (A)", value=None, placeholder="Ex: 18.0", key=f"icc_n_{i}")
                imp = c2.number_input(f"Imp MPPT {i} (A)", value=None, placeholder="Ex: 13.5", key=f"imp_n_{i}")
                str_n = c3.number_input(f"Strings MPPT {i}", value=1, step=1, key=f"str_n_{i}")
                if icc is not None:
                    mppts_payload.append({"mppt_numero": i, "icc_a": icc, "imp_a": imp or icc, "max_strings": int(str_n)})

            if st.form_submit_button("Salvar Novo Inversor"):
                if not all([sku, fab, mod, pmax, vmax, vmin]) or len(mppts_payload) < int(qtd_mppts):
                    st.error("Preencha todos os campos corretamente!")
                else:
                    data = {
                        "sku": sku, "fabricante": fab, "modelo": mod,
                        "pnom_kw": pnom or 0.0, "pmax_w": pmax, "vmax_v": vmax, "vmin_v": vmin,
                        "disponivel": disp_inicial, "mppts": mppts_payload
                    }
                    res = requests.post(f"{API_URL}/inversores/", json=data, headers=get_headers())
                    if res.status_code == 201:
                        st.cache_data.clear()
                        st.success("Inversor cadastrado com sucesso!")
                        st.rerun()