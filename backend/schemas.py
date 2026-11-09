from pydantic import BaseModel
from typing import List, Optional

# Auth
class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

# Painel
class PainelCreate(BaseModel):
    sku: str = "-"
    fabricante: str
    modelo: str
    potencia_wp: float
    voc_v: float
    vmp_v: float
    isc_a: float
    imp_a: float = 0.0
    coef_temp_voc: float = -0.28
    disponivel: bool = True

class PainelResponse(PainelCreate):
    id: int
    class Config:
        from_attributes = True

# MPPT do Inversor
class MPPTCreate(BaseModel):
    mppt_numero: int
    icc_a: float
    imp_a: float
    max_strings: int

class MPPTResponse(MPPTCreate):
    id: int
    class Config:
        from_attributes = True

# Inversor
class InversorCreate(BaseModel):
    sku: str = "-"
    fabricante: str
    modelo: str
    pnom_kw: float
    pmax_w: float
    vmax_v: float
    vmin_v: float
    disponivel: bool = True
    mppts: List[MPPTCreate]

class InversorResponse(BaseModel):
    id: int
    sku: str
    fabricante: str
    modelo: str
    pnom_kw: float
    pmax_w: float
    vmax_v: float
    vmin_v: float
    disponivel: bool
    mppts: List[MPPTResponse]
    class Config:
        from_attributes = True

# Requisição de Cálculo
class DimensionamentoRequest(BaseModel):
    temp_min: float = 0.0
    temp_max: float = 75.0
    painel_ids: Optional[List[int]] = None   # None ou vazio -> Todos os painéis
    inversor_ids: Optional[List[int]] = None # None ou vazio -> Todos os inversores