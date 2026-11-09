import pandas as pd
import os
from database import SessionLocal, engine
import models, auth

models.Base.metadata.create_all(bind=engine)

PLANILHA = "calculo_mppt.xlsx" 

def migrar_planilha():
    if not os.path.exists(PLANILHA):
        print(f"❌ Planilha {PLANILHA} não encontrada.")
        return

    db = SessionLocal()

    # 1. Criar Admin se não existir
    if not db.query(models.User).filter(models.User.username == "admin").first():
        db.add(models.User(username="admin", password_hash=auth.get_password_hash("admin123"), role="admin"))
        db.commit()
        print("✅ Usuário admin criado.")

    xl = pd.ExcelFile(PLANILHA)
    df_raw = pd.read_excel(xl, sheet_name="MPPT", header=1)
    df_raw.columns = [str(c).strip() for c in df_raw.columns]

    # --- 2. IMPORTAÇÃO DOS PAINÉIS ---
    df_p = df_raw.dropna(subset=['Módulo', 'Pot']).copy()
    col_sku_p = [c for c in df_p.columns if 'sku_p' in c.lower()]
    col_disp_p = [c for c in df_p.columns if c.lower() == 'disponivel_p']

    paineis_cadastrados = 0
    modelos_paineis_vistos = set()

    for _, r in df_p.iterrows():
        mod_nome = str(r['Módulo']).strip()
        
        # Evita tentar inserir o mesmo modelo de painel duas vezes
        if mod_nome in modelos_paineis_vistos:
            continue
        modelos_paineis_vistos.add(mod_nome)

        sku = str(r[col_sku_p[0]]).strip() if col_sku_p and pd.notna(r[col_sku_p[0]]) else "-"
        disp = True
        if col_disp_p and pd.notna(r[col_disp_p[0]]):
            disp = str(r[col_disp_p[0]]).strip().upper() == "SIM"

        if not db.query(models.Painel).filter(models.Painel.modelo == mod_nome).first():
            painel = models.Painel(
                sku=sku,
                fabricante=mod_nome.split()[0] if mod_nome else "Genérico",
                modelo=mod_nome,
                potencia_wp=float(r['Pot']),
                voc_v=float(r['Voc']),
                vmp_v=float(r['Vmp']),
                isc_a=float(r['Icc']) if 'Icc' in r and pd.notna(r['Icc']) else float(r.get('Isc', 0.0)),
                imp_a=float(r.get('Imp', 0.0)),
                coef_temp_voc=float(r['%']) if '%' in r and pd.notna(r['%']) else -0.28,
                disponivel=disp
            )
            db.add(painel)
            db.commit()
            paineis_cadastrados += 1

    # --- 3. IMPORTAÇÃO DOS INVERSORES COM MPPTS ---
    df_i = df_raw.dropna(subset=['Inversor', 'Pmax']).copy()
    col_sku_i = [c for c in df_i.columns if 'sku_i' in c.lower()]
    col_disp_i = [c for c in df_i.columns if c.lower() == 'disponivel_i']

    inversores_cadastrados = 0
    modelos_inversores_vistos = set()

    for _, r in df_i.iterrows():
        inv_nome = str(r['Inversor']).strip()
        
        # Evita tentar inserir o mesmo modelo de inversor duas vezes
        if inv_nome in modelos_inversores_vistos:
            continue
        modelos_inversores_vistos.add(inv_nome)

        sku = str(r[col_sku_i[0]]).strip() if col_sku_i and pd.notna(r[col_sku_i[0]]) else "-"
        disp = True
        if col_disp_i and pd.notna(r[col_disp_i[0]]):
            disp = str(r[col_disp_i[0]]).strip().upper() == "SIM"

        if not db.query(models.Inversor).filter(models.Inversor.modelo == inv_nome).first():
            inversor = models.Inversor(
                sku=sku,
                fabricante=inv_nome.split()[0] if inv_nome else "Genérico",
                modelo=inv_nome,
                pnom_kw=float(r.get('Pnom', 0.0)),
                pmax_w=float(r['Pmax']),
                vmax_v=float(r['Vmax']),
                vmin_v=float(r['Vmin']),
                disponivel=disp
            )

            # Extrai até 15 MPPTs dinamicamente
            for i in range(1, 16):
                col_icc = f"Icc {i}"
                col_imp = f"Imp {i}"
                cols_str = [c for c in r.index if str(c).strip() in [str(i), f"{i}.0"]]

                if col_icc in r and pd.notna(r[col_icc]):
                    icc_val = float(r[col_icc])
                    imp_val = float(r[col_imp]) if col_imp in r and pd.notna(r[col_imp]) else icc_val
                    n_strings = 1
                    if cols_str and pd.notna(r[cols_str[0]]):
                        n_strings = int(float(r[cols_str[0]]))

                    if n_strings > 0:
                        inversor.mppts.append(models.InversorMPPT(
                            mppt_numero=i,
                            icc_a=icc_val,
                            imp_a=imp_val,
                            max_strings=n_strings
                        ))

            db.add(inversor)
            db.commit()
            inversores_cadastrados += 1

    db.close()
    print(f"🚀 Sucesso! {paineis_cadastrados} Painéis e {inversores_cadastrados} Inversores migrados para o PostgreSQL.")

if __name__ == "__main__":
    migrar_planilha()