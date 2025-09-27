from __future__ import annotations

from sqlalchemy import String, Integer, Float, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional, Dict, Any

from .database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    price: Mapped[float] = mapped_column(Float, default=0.0)
    site_id: Mapped[str] = mapped_column(String(8), default="MLA")
    currency_id: Mapped[str] = mapped_column(String(8), default="ARS")
    sold_quantity: Mapped[int] = mapped_column(Integer, default=0)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)
    
    # Nuevos campos
    marca: Mapped[str] = mapped_column(String(100), default="")
    modelo: Mapped[str] = mapped_column(String(100), default="")
    caracteristicas: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Información adicional de MercadoLibre
    ml_additional_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)


