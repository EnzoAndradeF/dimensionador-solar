import streamlit as st 
import pandas as pd 
import math 
import io 
import os
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
    
    df_p = pd.read_excel(xl, sheet_name="MPPT", header=1, usecols="BC:BK").dropna(subset=['Módulo', 'Pot'])
    df_i = pd.read_excel(xl, sheet_name="MPPT", header=1, usecols="BK:DL").dropna(subset=['Inversor', 'Pmax'])
    
    df_p.columns = [str(c).strip() for c in df_p.columns]
    df_i.columns = [str(c).strip() for c in df_i.columns]

    # Aplica o filtro de loja apenas se o checkbox estiver marcado
    if apenas_loja:
        col_loja_p = [c for c in df_p.columns if c.lower() == 'disponivel_p']
        if col_loja_p:
            df_p = df_p[df_p[col_loja_p[0]].astype(str).str.strip().str.upper().isin(['SIM'])]

        col_loja_i = [c for c in df_i.columns if c.lower() == 'disponivel_i']
        if col_loja_i:
            for c in col_loja_i:
                df_i = df_i[df_i[c].astype(str).str.strip().str.upper().isin(['SIM'])]

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

        # Cria a coluna formatada para facilidade de filtro
        df_paineis['opcao_formatada'] = df_paineis.apply(lambda r: formatar_opcao(r, 'Módulo', sku_p_cols), axis=1)
        df_inversores['opcao_formatada'] = df_inversores.apply(lambda r: formatar_opcao(r, 'Inversor', sku_i_cols), axis=1)

        lista_paineis = ["Todos"] + df_paineis['opcao_formatada'].tolist()
        lista_inversores = ["Todos"] + df_inversores['opcao_formatada'].tolist()

        # Substituído por multiselect
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

        def calcular_quantitativo(df_p, df_i, t_min, t_max, sel_p, sel_i):
            # Se não selecionou nada ou marcou "Todos", considera a base completa
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
                coeff_p = float(p['%'])

                voc_corrigida = voc_p + (voc_p * (coeff_p / 100.0) * (t_min - 25))
                vmp_corrigida = vmp_p + (vmp_p * (coeff_p / 100.0) * (t_max - 25))

                for _, inv in df_i.iterrows():
                    sku_inversor = inv[sku_i_cols[0]] if sku_i_cols and pd.notna(inv[sku_i_cols[0]]) else '-'
                    modelo_inv = str(inv['Inversor']).strip()
                    pmax_inv = float(inv['Pmax'])
                    vmax_inv = float(inv['Vmax'])
                    vmin_mppt = float(inv['Vmin'])
                    
                    max_string = math.floor(vmax_inv / voc_corrigida) if voc_corrigida > 0 else 0
                    min_string = math.ceil(vmin_mppt / vmp_corrigida) if vmp_corrigida > 0 else 0
                    max_total_potencia = math.floor(pmax_inv / pot_p) if pot_p > 0 else 0

                    if min_string > max_string or max_string == 0:
                        status = "Incompatível (Faixa Tensão Inválida)"
                        max_total_final = 0
                        pot_min_kwp = 0.0
                        pot_max_kwp = 0.0
                    else:
                        status = "Compatível"
                        max_total_final = max_total_potencia
                        pot_min_kwp = round((min_string * pot_p) / 1000.0, 2)
                        pot_max_kwp = round((max_total_final * pot_p) / 1000.0, 2)

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
                        "Máx. Painéis / Inversor": max_total_final,
                        "Pot. Máxima (kWp)": pot_max_kwp
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
                        "Mín. Módulos / String",
                        "Pot. Mínima (kWp)",
                        "Máx. Painéis / Inversor",
                        "Pot. Máxima (kWp)"
                    ]
                    
                    df_excel = df_res[colunas_relatorio]

                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_excel.to_excel(writer, index=False, sheet_name='Quantitativo_Estoque')

                    # Formatação dinâmica da data/hora de emissão
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