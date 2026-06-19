# backend/models/transformer.py
# This class becomes the "transformers" table in PostgreSQL.
# Each field = one column in the table.

from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func
from database import Base

class Transformer(Base):
    __tablename__ = "transformers"

    id               = Column(Integer, primary_key=True, index=True)
    transformer_id   = Column(String(20), unique=True, nullable=False, index=True)
    name             = Column(String(100))
    substation_name  = Column(String(100))
    district         = Column(String(50))
    latitude         = Column(Numeric(9, 6))   # GPS lat — for the map
    longitude        = Column(Numeric(9, 6))   # GPS lng — for the map
    capacity_kva     = Column(Integer)          # max load capacity
    installation_year = Column(Integer)
    manufacturer     = Column(String(100))
    created_at       = Column(DateTime(timezone=True), server_default=func.now())