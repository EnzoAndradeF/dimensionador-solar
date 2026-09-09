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
st.markdown("Base de dados filtrada por **Disponivel = Sim**. Selecione os equipamentos desejados na barra lateral.")

st.sidebar.header("Parâmetros Globais")
t_min = st.sidebar.number_input("T. Mínima Ambiente (°C)", value=0)
t_max = st.sidebar.number_input("T. Máxima Painel (°C)", value=75)

PLANILHA = "calculo_mppt.xlsx"

# O prefixo '_' no parâmetro _mtime indica ao Streamlit para não fazer hash desse argumento especificamente
@st.cache_data
def carregar_dados_limpos(caminho, _mtime):
    xl = pd.ExcelFile(caminho)
    
    df_p = pd.read_excel(xl, sheet_name="MPPT", header=1, usecols="BC:BK").dropna(subset=['Módulo', 'Pot'])
    df_i = pd.read_excel(xl, sheet_name="MPPT", header=1, usecols="BK:DL").dropna(subset=['Inversor', 'Pmax'])
    
    df_p.columns = [str(c).strip() for c in df_p.columns]
    df_i.columns = [str(c).strip() for c in df_i.columns]

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
        df_paineis, df_inversores = carregar_dados_limpos(PLANILHA, _mtime=mtime_planilha)

        st.sidebar.header("Seleção de Equipamentos")

        sku_p_cols = [c for c in df_paineis.columns if 'sku_p' in c.lower()]
        sku_i_cols = [c for c in df_inversores.columns if 'sku_i' in c.lower()]

        # Função auxiliar para formatar a string de exibição do equipamento
        def formatar_opcao(row, col_nome, sku_cols):
            nome = str(row[col_nome]).strip()
            if sku_cols and pd.notna(row[sku_cols[0]]):
                return f"[{row[sku_cols[0]]}] {nome}"
            return nome

        # Listas de opções formatadas
        opcoes_paineis = [formatar_opcao(r, 'Módulo', sku_p_cols) for _, r in df_paineis.iterrows()]
        opcoes_inversores = [formatar_opcao(r, 'Inversor', sku_i_cols) for _, r in df_inversores.iterrows()]

        # Seleção Múltipla com 'multiselect'
        st.sidebar.markdown("**Painéis:** *(deixe vazio ou selecione 'Todos' para incluir todos)*")
        paineis_selecionados = st.sidebar.multiselect(
            "Filtrar Painéis:",
            options=["Todos"] + opcoes_paineis,
            default=["Todos"]
        )

        st.sidebar.markdown("**Inversores:** *(deixe vazio ou selecione 'Todos' para incluir todos)*")
        inversores_selecionados = st.sidebar.multiselect(
            "Filtrar Inversores:",
            options=["Todos"] + opcoes_inversores,
            default=["Todos"]
        )

        def calcular_quantitativo(df_p, df_i, t_min, t_max, sel_p, sel_i):
            # Lógica de filtro flexível para Painéis
            if sel_p and "Todos" not in sel_p:
                df_p = df_p[df_p.apply(lambda r: formatar_opcao(r, 'Módulo', sku_p_cols) in sel_p, axis=1)]

            # Lógica de filtro flexível para Inversores
            if sel_i and "Todos" not in sel_i:
                df_i = df_i[df_i.apply(lambda r: formatar_opcao(r, 'Inversor', sku_i_cols) in sel_i, axis=1)]

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
                    else:
                        status = "Compatível"
                        max_total_final = max_total_potencia

                    resultados.append({
                        "SKU Painel": sku_painel,
                        "Painel": modulo,
                        "SKU Inversor": sku_inversor,
                        "Inversor": modelo_inv,
                        "Status": status,
                        "Mín. Módulos / String": min_string,
                        "Máx. Painéis / Inversor": max_total_final
                    })

            return pd.DataFrame(resultados)

        # Botão para processar
        if st.button("Processar Quantitativo", type="primary"):
            with st.spinner("Calculando arranjos..."):
                df_res = calcular_quantitativo(df_paineis, df_inversores, t_min, t_max, paineis_selecionados, inversores_selecionados)
                st.session_state['df_resultado'] = df_res

        # Exibição e Download do Resultado
        if 'df_resultado' in st.session_state:
            df_res = st.session_state['df_resultado']

            if df_res.empty:
                st.warning("Nenhum item encontrado para a seleção realizada.")
            else:
                st.success(f"Concluído! {len(df_res)} combinação(ões) gerada(s).")
                st.dataframe(df_res, use_container_width=True)

                # Gera o arquivo Excel em memória
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_res.to_excel(writer, index=False, sheet_name='Quantitativo_Estoque')

                # Nome dinâmico com Data e Hora
                data_hora_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                nome_relatorio = f"Quantitativo_MPPT_{data_hora_str}.xlsx"

                st.download_button(
                    label="📥 Baixar Relatório (Excel)",
                    data=buffer.getvalue(),
                    file_name=nome_relatorio,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")

else:
    st.error(f"Arquivo '{PLANILHA}' não encontrado na pasta do projeto.")