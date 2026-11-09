import math
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload

import models, schemas, auth
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Dimensionador Solar - Sou Energy")

# --- AUTH (APENAS PARA ADMIN) ---
@app.post("/auth/register", response_model=schemas.UserResponse)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")
    hashed_pwd = auth.get_password_hash(user_in.password)
    new_user = models.User(username=user_in.username, password_hash=hashed_pwd, role=user_in.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Usuário ou senha incorretos")
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=auth.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

# --- CONSULTAS PÚBLICAS ---
@app.get("/paineis/", response_model=List[schemas.PainelResponse])
def listar_paineis(apenas_disponiveis: bool = False, db: Session = Depends(get_db)):
    query = db.query(models.Painel)
    if apenas_disponiveis:
        query = query.filter(models.Painel.disponivel == True)
    return query.all()

@app.get("/inversores/", response_model=List[schemas.InversorResponse])
def listar_inversores(apenas_disponiveis: bool = False, db: Session = Depends(get_db)):
    query = db.query(models.Inversor).options(joinedload(models.Inversor.mppts))
    if apenas_disponiveis:
        query = query.filter(models.Inversor.disponivel == True)
    return query.all()

# --- CADASTROS E MANUTENÇÃO (REQUER ADMIN) ---
@app.post("/paineis/", response_model=schemas.PainelResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_painel(painel: schemas.PainelCreate, db: Session = Depends(get_db), admin = Depends(auth.require_admin)):
    novo_painel = models.Painel(**painel.model_dump())
    db.add(novo_painel)
    db.commit()
    db.refresh(novo_painel)
    return novo_painel

@app.put("/paineis/{painel_id}", response_model=schemas.PainelResponse)
def atualizar_painel(painel_id: int, painel_in: schemas.PainelCreate, db: Session = Depends(get_db), admin = Depends(auth.require_admin)):
    painel = db.query(models.Painel).filter(models.Painel.id == painel_id).first()
    if not painel:
        raise HTTPException(status_code=404, detail="Painel não encontrado")
    
    for key, value in painel_in.model_dump().items():
        setattr(painel, key, value)
    
    db.commit()
    db.refresh(painel)
    return painel

@app.delete("/paineis/{painel_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_painel(painel_id: int, db: Session = Depends(get_db), admin = Depends(auth.require_admin)):
    painel = db.query(models.Painel).filter(models.Painel.id == painel_id).first()
    if not painel:
        raise HTTPException(status_code=404, detail="Painel não encontrado")
    db.delete(painel)
    db.commit()
    return None

@app.post("/inversores/", response_model=schemas.InversorResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_inversor(inversor: schemas.InversorCreate, db: Session = Depends(get_db), admin = Depends(auth.require_admin)):
    mppts_data = inversor.mppts
    inversor_dict = inversor.model_dump(exclude={"mppts"})
    novo_inversor = models.Inversor(**inversor_dict)
    
    for mppt_item in mppts_data:
        novo_mppt = models.InversorMPPT(**mppt_item.model_dump())
        novo_inversor.mppts.append(novo_mppt)

    db.add(novo_inversor)
    db.commit()
    db.refresh(novo_inversor)
    return novo_inversor

@app.put("/inversores/{inversor_id}", response_model=schemas.InversorResponse)
def atualizar_inversor(inversor_id: int, inversor_in: schemas.InversorCreate, db: Session = Depends(get_db), admin = Depends(auth.require_admin)):
    inversor = db.query(models.Inversor).options(joinedload(models.Inversor.mppts)).filter(models.Inversor.id == inversor_id).first()
    if not inversor:
        raise HTTPException(status_code=404, detail="Inversor não encontrado")
    
    inversor_data = inversor_in.model_dump(exclude={"mppts"})
    for key, value in inversor_data.items():
        setattr(inversor, key, value)
    
    db.query(models.InversorMPPT).filter(models.InversorMPPT.inversor_id == inversor_id).delete()
    for mppt_item in inversor_in.mppts:
        novo_mppt = models.InversorMPPT(**mppt_item.model_dump())
        inversor.mppts.append(novo_mppt)

    db.commit()
    db.refresh(inversor)
    return inversor

@app.delete("/inversores/{inversor_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_inversor(inversor_id: int, db: Session = Depends(get_db), admin = Depends(auth.require_admin)):
    inversor = db.query(models.Inversor).filter(models.Inversor.id == inversor_id).first()
    if not inversor:
        raise HTTPException(status_code=404, detail="Inversor não encontrado")
    db.delete(inversor)
    db.commit()
    return None

@app.patch("/paineis/{painel_id}/disponibilidade")
def atualizar_disponibilidade_painel(painel_id: int, disponivel: bool, db: Session = Depends(get_db), admin = Depends(auth.require_admin)):
    painel = db.query(models.Painel).filter(models.Painel.id == painel_id).first()
    if not painel:
        raise HTTPException(status_code=404, detail="Painel não encontrado")
    painel.disponivel = disponivel
    db.commit()
    return {"message": "Status atualizado", "disponivel": painel.disponivel}

@app.patch("/inversores/{inversor_id}/disponibilidade")
def atualizar_disponibilidade_inversor(inversor_id: int, disponivel: bool, db: Session = Depends(get_db), admin = Depends(auth.require_admin)):
    inversor = db.query(models.Inversor).filter(models.Inversor.id == inversor_id).first()
    if not inversor:
        raise HTTPException(status_code=404, detail="Inversor não encontrado")
    inversor.disponivel = disponivel
    db.commit()
    return {"message": "Status atualizado", "disponivel": inversor.disponivel}

# --- CÁLCULO PÚBLICO ---
@app.post("/dimensionar/")
def calcular_quantitativo(req: schemas.DimensionamentoRequest, db: Session = Depends(get_db)):
    query_p = db.query(models.Painel)
    if req.painel_ids:
        query_p = query_p.filter(models.Painel.id.in_(req.painel_ids))
    paineis = query_p.all()

    query_i = db.query(models.Inversor).options(joinedload(models.Inversor.mppts))
    if req.inversor_ids:
        query_i = query_i.filter(models.Inversor.id.in_(req.inversor_ids))
    inversores = query_i.all()

    resultados = []

    for p in paineis:
        pot_p = float(p.potencia_wp or 0.0)
        voc_p = float(p.voc_v or 0.0)
        vmp_p = float(p.vmp_v or 0.0)
        icc_p = float(p.isc_a or 0.0)
        coeff_p = float(p.coef_temp_voc or -0.28)

        voc_corrigida = voc_p + (voc_p * (coeff_p / 100.0) * (req.temp_min - 25))
        vmp_corrigida = vmp_p + (vmp_p * (coeff_p / 100.0) * (req.temp_max - 25))

        for inv in inversores:
            pmax_inv = float(inv.pmax_w or 0.0)
            vmax_inv = float(inv.vmax_v or 0.0)
            vmin_mppt = float(inv.vmin_v or 0.0)
            mppts_sorted = sorted(inv.mppts, key=lambda x: x.mppt_numero)

            max_string = math.floor(vmax_inv / voc_corrigida) if voc_corrigida > 0 else 0
            min_string = math.ceil(vmin_mppt / vmp_corrigida) if vmp_corrigida > 0 else 0

            compativel = True
            if voc_corrigida > vmax_inv:
                status_str = "Incompatível (Voc Excede Vmax do Inversor)"
                compativel = False

            if compativel and mppts_sorted:
                for mppt in mppts_sorted:
                    if icc_p > float(mppt.icc_a or 0.0):
                        status_str = f"Incompatível (Icc Painel {icc_p}A > MPPT{mppt.mppt_numero} {mppt.icc_a}A)"
                        compativel = False
                        break

            if compativel:
                if min_string > max_string or max_string == 0:
                    status_str = "Incompatível (Faixa de Tensão Indisponível)"
                    compativel = False

            if not compativel:
                resultados.append({
                    "SKU Painel": p.sku,
                    "Painel": f"{p.fabricante} {p.modelo}",
                    "SKU Inversor": inv.sku,
                    "Inversor": f"{inv.fabricante} {inv.modelo}",
                    "Status": status_str,
                    "Mín. Módulos / String": 0,
                    "Máx. Painéis / String": 0,
                    "Máx. Painéis / Inversor": 0,
                    "Arranjo/Combinação": "N/A",
                    "Potência Painel (W)": pot_p,
                    "Voc Corrigido (V)": round(voc_corrigida, 2),
                    "Vmp Corrigido (V)": round(vmp_corrigida, 2),
                    "Pmax Inversor (W)": pmax_inv,
                    "Vmax Inversor (V)": vmax_inv,
                    "Vmin MPPT (V)": vmin_mppt,
                    "Pot. Mínima (kWp)": 0.0,
                    "Pot. Máxima (kWp)": 0.0
                })
                continue

            melhor_total_paineis = 0
            melhor_potencia = 0.0
            melhor_arranjo_str = ""

            tamanhos_validos = sorted(list(range(min_string, max_string + 1)), reverse=True)

            for tam_principal in tamanhos_validos:
                acumulado_paineis = 0
                arranjo_temp = []

                for mppt in mppts_sorted:
                    mppt_icc = float(mppt.icc_a or 0.0)
                    max_str_corrente = math.floor(mppt_icc / icc_p) if icc_p > 0 else 0
                    str_permitidas = min(int(mppt.max_strings or 1), max_str_corrente)

                    alocado_mppt = (0, 0)

                    for n_str in range(str_permitidas, 0, -1):
                        p_test = (acumulado_paineis + n_str * tam_principal) * pot_p
                        if p_test <= pmax_inv:
                            alocado_mppt = (n_str, tam_principal)
                            break

                    if alocado_mppt == (0, 0) and str_permitidas > 0:
                        for tam_secundario in tamanhos_validos:
                            if tam_secundario >= tam_principal:
                                continue
                            for n_str in range(str_permitidas, 0, -1):
                                p_test = (acumulado_paineis + n_str * tam_secundario) * pot_p
                                if p_test <= pmax_inv:
                                    alocado_mppt = (n_str, tam_secundario)
                                    break
                            if alocado_mppt != (0, 0):
                                break

                    n_str, tam_str = alocado_mppt
                    if n_str > 0:
                        acumulado_paineis += n_str * tam_str
                        arranjo_temp.append((mppt.mppt_numero, n_str, tam_str))

                pot_total = acumulado_paineis * pot_p
                if acumulado_paineis > melhor_total_paineis and pot_total <= pmax_inv:
                    melhor_total_paineis = acumulado_paineis
                    melhor_potencia = pot_total
                    detalhes = [f"MPPT{m_id}: {n_str}x{tam_str}" for m_id, n_str, tam_str in arranjo_temp]
                    melhor_arranjo_str = " | ".join(detalhes)

            if melhor_total_paineis > 0:
                status_str = "Compatível"
                pot_min_kwp = round((min_string * pot_p) / 1000.0, 2)
                pot_max_kwp = round(melhor_potencia / 1000.0, 2)
            else:
                status_str = "Incompatível (Não encaixa na Pmax do Inversor)"
                pot_min_kwp = 0.0
                pot_max_kwp = 0.0

            resultados.append({
                "SKU Painel": p.sku,
                "Painel": f"{p.fabricante} {p.modelo}",
                "SKU Inversor": inv.sku,
                "Inversor": f"{inv.fabricante} {inv.modelo}",
                "Status": status_str,
                "Mín. Módulos / String": min_string,
                "Máx. Painéis / String": max_string,
                "Máx. Painéis / Inversor": melhor_total_paineis,
                "Arranjo/Combinação": melhor_arranjo_str if melhor_total_paineis > 0 else "N/A",
                "Potência Painel (W)": pot_p,
                "Voc Corrigido (V)": round(voc_corrigida, 2),
                "Vmp Corrigido (V)": round(vmp_corrigida, 2),
                "Pmax Inversor (W)": pmax_inv,
                "Vmax Inversor (V)": vmax_inv,
                "Vmin MPPT (V)": vmin_mppt,
                "Pot. Mínima (kWp)": pot_min_kwp,
                "Pot. Máxima (kWp)": pot_max_kwp
            })

    return resultados

# Compatibilidade de painéis

@app.get("/paineis/todos/")
def listar_todos_paineis(db: Session = Depends(get_db)):
    """Retorna TODOS os painéis cadastrados no banco (disponíveis ou não)."""
    return db.query(models.Painel).all()

@app.get("/paineis/comparar/")
def comparar_paineis(painel_a_id: int, painel_b_id: int, db: Session = Depends(get_db)):
    painel_a = db.query(models.Painel).filter(models.Painel.id == painel_a_id).first()
    painel_b = db.query(models.Painel).filter(models.Painel.id == painel_b_id).first()

    if not painel_a or not painel_b:
        raise HTTPException(status_code=404, detail="Um ou ambos os painéis não foram encontrados.")

    def calc_diff(val_a, val_b):
        if val_a == 0:
            return 0.0
        return round(abs(val_a - val_b) / val_a * 100, 2)

    diff_voc = calc_diff(painel_a.voc_v, painel_b.voc_v)
    diff_vmp = calc_diff(painel_a.vmp_v, painel_b.vmp_v)
    diff_isc = calc_diff(painel_a.isc_a, painel_b.isc_a)
    diff_imp = calc_diff(painel_a.imp_a, painel_b.imp_a)

    # Regra dos 5%
    compativel = (
        diff_voc <= 5.0 and 
        diff_vmp <= 5.0 and 
        diff_isc <= 5.0 and 
        diff_imp <= 5.0
    )

    return {
        "compativel": compativel,
        "detalhes": {
            "voc": {"painel_a": painel_a.voc_v, "painel_b": painel_b.voc_v, "diff_pct": diff_voc, "ok": diff_voc <= 5.0},
            "vmp": {"painel_a": painel_a.vmp_v, "painel_b": painel_b.vmp_v, "diff_pct": diff_vmp, "ok": diff_vmp <= 5.0},
            "isc": {"painel_a": painel_a.isc_a, "painel_b": painel_b.isc_a, "diff_pct": diff_isc, "ok": diff_isc <= 5.0},
            "imp": {"painel_a": painel_a.imp_a, "painel_b": painel_b.imp_a, "diff_pct": diff_imp, "ok": diff_imp <= 5.0},
        }
    }