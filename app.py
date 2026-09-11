import streamlit as st 
import pandas as pd 
import math 
import io 
import os
import itertools
from datetime import datetime

st.set_page_config(
    page_title="Quantitativo de Painéis por MPPT - Sou Energy",
    layout="wide"
)

st.title("Quantitativo de Painéis por Inversor - Sou Energy")

st.sidebar.header("Parâmetros Globais")
t_min = st.sidebar.number_input("T. Mínima Ambiente (°C)", value=0)
t_max = st.sidebar.number_input("T. Máxima Painel (°C)", value=75)

# Filtro para alternar entre itens de loja vs. catálogo completo
apenas_em_loja = st.sidebar.checkbox("Apenas Equipamentos em Loja?", value=True)

PLANILHA = "calculo_mppt.xlsx"

@st.cache_data
def carregar_dados_limpos(caminho, apenas_loja, _mtime):
    xl = pd.ExcelFile(caminho)
    
    # Lê toda a aba MPPT sem travar colunas fixas por letra (A, B, BC, etc.)
    df_raw = pd.read_excel(xl, sheet_name="MPPT", header=1)
    df_raw.columns = [str(c).strip() for c in df_raw.columns]

    # --- 1. SEPARAÇÃO E FILTRAGEM DOS PAINÉIS ---
    colunas_obr_painel = ['Módulo', 'Pot', 'Voc', 'Vmp', '%']
    cols_p = [c for c in colunas_obr_painel if c in df_raw.columns]
    
    if len(cols_p) < len(colunas_obr_painel):
        raise ValueError(f"Planilha sem as colunas obrigatórias de Painel: {colunas_obr_painel}")

    # Seleciona bloco de painéis filtrando linhas válidas
    df_p = df_raw.dropna(subset=['Módulo', 'Pot']).copy()

    # --- 2. SEPARAÇÃO E FILTRAGEM DOS INVERSORES ---
    colunas_obr_inversor = ['Inversor', 'Pmax', 'Vmax', 'Vmin']
    cols_i = [c for c in colunas_obr_inversor if c in df_raw.columns]

    if len(cols_i) < len(colunas_obr_inversor):
        raise ValueError(f"Planilha sem as colunas obrigatórias de Inversor: {colunas_obr_inversor}")

    df_i = df_raw.dropna(subset=['Inversor', 'Pmax']).copy()

    # --- 3. FILTRO DE DISPONIBILIDADE EM LOJA ---
    if apenas_loja:
        col_loja_p = [c for c in df_p.columns if c.lower() == 'disponivel_p']
        if col_loja_p:
            df_p = df_p[df_p[col_loja_p[0]].astype(str).str.strip().str.upper().isin(['SIM'])]

        col_loja_i = [c for c in df_i.columns if c.lower() == 'disponivel_i']
        if col_loja_i:
            df_i = df_i[df_i[col_loja_i[0]].astype(str).str.strip().str.upper().isin(['SIM'])]

    return df_p, df_i


if os.path.exists(PLANILHA):
    try:
        mtime_planilha = os.path.getmtime(PLANILHA)
        df_paineis, df_inversores = carregar_dados_limpos(
            PLANILHA, 
            apenas_loja=apenas_em_loja, 
            _mtime=mtime_planilha
        )

        st.sidebar.header("Seleção de Equipamentos")

        sku_p_cols = [c for c in df_paineis.columns if 'sku_p' in c.lower()]
        sku_i_cols = [c for c in df_inversores.columns if 'sku_i' in c.lower()]

        def formatar_opcao(row, col_nome, sku_cols):
            nome = str(row[col_nome]).strip()
            if sku_cols and pd.notna(row[sku_cols[0]]):
                return f"[{row[sku_cols[0]]}] {nome}"
            return nome

        # Cria colunas formatadas para a seleção
        df_paineis['opcao_formatada'] = df_paineis.apply(lambda r: formatar_opcao(r, 'Módulo', sku_p_cols), axis=1)
        df_inversores['opcao_formatada'] = df_inversores.apply(lambda r: formatar_opcao(r, 'Inversor', sku_i_cols), axis=1)

        lista_paineis = ["Todos"] + df_paineis['opcao_formatada'].tolist()
        lista_inversores = ["Todos"] + df_inversores['opcao_formatada'].tolist()

        paineis_selecionados = st.sidebar.multiselect(
            "Filtrar Painel(is):", 
            options=lista_paineis,
            default=["Todos"],
            help="Selecione um ou mais painéis. Deixe 'Todos' para considerar o catálogo inteiro."
        )
        
        inversores_selecionados = st.sidebar.multiselect(
            "Filtrar Inversor(es):", 
            options=lista_inversores,
            default=["Todos"],
            help="Selecione um ou mais inversores. Deixe 'Todos' para considerar o catálogo inteiro."
        )

        def extrair_mppts_inversor(row_inv):
            """Extrai a estrutura das MPPTs dinâmica para colunas tipo Icc 1..15 e 1..15."""
            mppts = []
            for i in range(1, 16):
                col_icc = f"Icc {i}"
                col_imp = f"Imp {i}"
                
                # Aceita nome de coluna '1', '1.0', etc.
                cols_str = [c for c in row_inv.index if str(c).strip() in [str(i), f"{i}.0"]]
                
                if col_icc in row_inv and pd.notna(row_inv[col_icc]):
                    icc = float(row_inv[col_icc])
                    imp = float(row_inv[col_imp]) if col_imp in row_inv and pd.notna(row_inv[col_imp]) else icc
                    
                    num_strings = 1
                    if cols_str and pd.notna(row_inv[cols_str[0]]):
                        num_strings = int(float(row_inv[cols_str[0]]))
                    
                    if num_strings > 0:
                        mppts.append({
                            'id': i,
                            'icc': icc,
                            'imp': imp,
                            'max_strings': num_strings
                        })
            return mppts

        def calcular_quantitativo(df_p, df_i, t_min, t_max, sel_p, sel_i):
            if sel_p and "Todos" not in sel_p:
                df_p = df_p[df_p['opcao_formatada'].isin(sel_p)]

            if sel_i and "Todos" not in sel_i:
                df_i = df_i[df_i['opcao_formatada'].isin(sel_i)]

            resultados = []

            for _, p in df_p.iterrows():
                sku_painel = p[sku_p_cols[0]] if sku_p_cols and pd.notna(p[sku_p_cols[0]]) else '-'
                modulo = str(p['Módulo']).strip()
                pot_p = float(p['Pot'])
                voc_p = float(p['Voc'])
                vmp_p = float(p['Vmp'])
                icc_p = float(p['Icc']) if 'Icc' in p and pd.notna(p['Icc']) else 0.0
                coeff_p = float(p['%'])

                # Correções térmicas de tensão
                voc_corrigida = voc_p + (voc_p * (coeff_p / 100.0) * (t_min - 25))
                vmp_corrigida = vmp_p + (vmp_p * (coeff_p / 100.0) * (t_max - 25))

                for _, inv in df_i.iterrows():
                    sku_inversor = inv[sku_i_cols[0]] if sku_i_cols and pd.notna(inv[sku_i_cols[0]]) else '-'
                    modelo_inv = str(inv['Inversor']).strip()
                    pmax_inv = float(inv['Pmax'])
                    vmax_inv = float(inv['Vmax'])
                    vmin_mppt = float(inv['Vmin'])
                    
                    mppts = extrair_mppts_inversor(inv)

                    # --- 1. VALIDAÇÃO DE SEGURANÇA ELÉTRICA ---
                    if voc_corrigida > vmax_inv:
                        status = "Incompatível (Voc Excede Vmax do Inversor)"
                        compativel = False
                    else:
                        compativel = True

                    if compativel and mppts:
                        for mppt in mppts:
                            if icc_p > mppt['icc']:
                                status = f"Incompatível (Icc Painel {icc_p}A > MPPT {mppt['icc']}A)"
                                compativel = False
                                break

                    if compativel:
                        max_string = math.floor(vmax_inv / voc_corrigida) if voc_corrigida > 0 else 0
                        min_string = math.ceil(vmin_mppt / vmp_corrigida) if vmp_corrigida > 0 else 0

                        if min_string > max_string or max_string == 0:
                            status = "Incompatível (Faixa de Tensão Indisponível)"
                            compativel = False

                    if not compativel:
                        resultados.append({
                            "SKU Painel": sku_painel,
                            "Painel": modulo,
                            "Potência Painel (W)": pot_p,
                            "Voc Corrigido (V)": round(voc_corrigida, 2),
                            "Vmp Corrigido (V)": round(vmp_corrigida, 2),
                            "SKU Inversor": sku_inversor,
                            "Inversor": modelo_inv,
                            "Pmax Inversor (W)": pmax_inv,
                            "Vmax Inversor (V)": vmax_inv,
                            "Vmin MPPT (V)": vmin_mppt,
                            "Status": status,
                            "Mín. Módulos / String": 0,
                            "Pot. Mínima (kWp)": 0.0,
                            "Máx. Painéis / Inversor": 0,
                            "Pot. Máxima (kWp)": 0.0,
                            "Arranjo/Combinação": "N/A"
                        })
                        continue

                    # --- 2. OTIMIZAÇÃO DE COMBINAÇÕES INDEPENDENTES POR MPPT ---
                    opcoes_por_mppt = []
                    for mppt in mppts:
                        max_str_corrente = math.floor(mppt['icc'] / icc_p) if icc_p > 0 else 0
                        max_str = min(mppt['max_strings'], max_str_corrente)
                        
                        opcoes_mppt = [(0, 0)]
                        for n_str in range(1, max_str + 1):
                            for tam_str in range(min_string, max_string + 1):
                                opcoes_mppt.append((n_str, tam_str))
                        
                        opcoes_por_mppt.append(opcoes_mppt)

                    melhor_total_paineis = 0
                    melhor_potencia = 0.0
                    melhor_arranjo_str = ""

                    for combinacao in itertools.product(*opcoes_por_mppt):
                        total_paineis = sum(n_str * tam_str for n_str, tam_str in combinacao)
                        potencia_total = total_paineis * pot_p

                        if potencia_total <= pmax_inv:
                            if total_paineis > melhor_total_paineis:
                                melhor_total_paineis = total_paineis
                                melhor_potencia = potencia_total
                                
                                detalhes = [
                                    f"MPPT{idx+1}: {n_str}x{tam_str}" 
                                    for idx, (n_str, tam_str) in enumerate(combinacao) if n_str > 0
                                ]
                                melhor_arranjo_str = " | ".join(detalhes)

                    if melhor_total_paineis > 0:
                        status = "Compatível"
                        pot_min_kwp = round((min_string * pot_p) / 1000.0, 2)
                        pot_max_kwp = round(melhor_potencia / 1000.0, 2)
                    else:
                        status = "Incompatível (Não encaixa na Pmax do Inversor)"
                        pot_min_kwp = 0.0
                        pot_max_kwp = 0.0

                    resultados.append({
                        "SKU Painel": sku_painel,
                        "Painel": modulo,
                        "Potência Painel (W)": pot_p,
                        "Voc Corrigido (V)": round(voc_corrigida, 2),
                        "Vmp Corrigido (V)": round(vmp_corrigida, 2),
                        "SKU Inversor": sku_inversor,
                        "Inversor": modelo_inv,
                        "Pmax Inversor (W)": pmax_inv,
                        "Vmax Inversor (V)": vmax_inv,
                        "Vmin MPPT (V)": vmin_mppt,
                        "Status": status,
                        "Mín. Módulos / String": min_string,
                        "Pot. Mínima (kWp)": pot_min_kwp,
                        "Máx. Painéis / Inversor": melhor_total_paineis,
                        "Pot. Máxima (kWp)": pot_max_kwp,
                        "Arranjo/Combinação": melhor_arranjo_str if melhor_total_paineis > 0 else "N/A"
                    })

            return pd.DataFrame(resultados)

        if st.button("Processar Quantitativo", type="primary"):
            with st.spinner("Calculando arranjos..."):
                df_res = calcular_quantitativo(
                    df_paineis, 
                    df_inversores, 
                    t_min, 
                    t_max, 
                    paineis_selecionados, 
                    inversores_selecionados
                )
                
                if df_res.empty:
                    st.warning("Nenhum item encontrado para a seleção realizada.")
                else:
                    st.success(f"Concluído! {len(df_res)} combinação(ões) gerada(s).")
                    
                    st.dataframe(df_res, use_container_width=True)

                    colunas_relatorio = [
                        "SKU Painel",
                        "Painel",
                        "SKU Inversor",
                        "Inversor",
                        "Status",
                        "Mín. Módulos / String",
                        "Pot. Mínima (kWp)",
                        "Máx. Painéis / Inversor",
                        "Pot. Máxima (kWp)",
                        "Arranjo/Combinação"
                    ]
                    
                    df_excel = df_res[colunas_relatorio]

                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_excel.to_excel(writer, index=False, sheet_name='Quantitativo_Estoque')

                    data_emissao = datetime.now().strftime("%Y-%m-%d_%H-%M")
                    nome_arquivo = f"Quantitativo_{data_emissao}.xlsx"

                    st.download_button(
                        label="📥 Baixar Relatório (Excel)",
                        data=buffer.getvalue(),
                        file_name=nome_arquivo,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")

else:
    st.error(f"Arquivo '{PLANILHA}' não encontrado na pasta do projeto.")