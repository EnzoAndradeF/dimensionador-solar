from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")

class Painel(Base):
    __tablename__ = "paineis"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, default="-")
    fabricante = Column(String, nullable=False)
    modelo = Column(String, unique=True, index=True, nullable=False)
    potencia_wp = Column(Float, nullable=False)
    voc_v = Column(Float, nullable=False)
    vmp_v = Column(Float, nullable=False)
    isc_a = Column(Float, nullable=False)
    imp_a = Column(Float, default=0.0)
    coef_temp_voc = Column(Float, default=-0.28) # Coeficiente em %/°C
    disponivel = Column(Boolean, default=True)

class Inversor(Base):
    __tablename__ = "inversores"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, default="-")
    fabricante = Column(String, nullable=False)
    modelo = Column(String, unique=True, index=True, nullable=False)
    pnom_kw = Column(Float, default=0.0)
    pmax_w = Column(Float, nullable=False) # Pmax em Watts para conferência exata
    vmax_v = Column(Float, nullable=False)
    vmin_v = Column(Float, nullable=False)
    disponivel = Column(Boolean, default=True)

    # Relacionamento 1:N com as MPPTs do inversor
    mppts = relationship("InversorMPPT", back_populates="inversor", cascade="all, delete-orphan")

class InversorMPPT(Base):
    __tablename__ = "inversor_mppts"

    id = Column(Integer, primary_key=True, index=True)
    inversor_id = Column(Integer, ForeignKey("inversores.id"))
    mppt_numero = Column(Integer, nullable=False) # Ex: MPPT 1, MPPT 2
    icc_a = Column(Float, nullable=False)          # Icc MPPT N (da imagem)
    imp_a = Column(Float, nullable=False)          # Imp MPPT N (da imagem)
    max_strings = Column(Integer, nullable=False)  # String MPPT N (da imagem)

    inversor = relationship("Inversor", back_populates="mppts")