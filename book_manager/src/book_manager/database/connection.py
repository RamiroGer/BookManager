"""Conexión a la base de datos de Supabase (PostgreSQL) con SQLAlchemy."""
from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

VARIABLE_URL: str = "SQLALCHEMY_DATABASE_URL"


class ConexionDB:
  """Administra el motor, las tablas y las sesiones de SQLAlchemy."""

  def __init__(self, url: Optional[str] = None) -> None:
    url_final: Optional[str] = url or os.getenv(VARIABLE_URL)
    if not url_final:
      raise ValueError(
        f"Falta la variable {VARIABLE_URL} con la URL de conexión."
      )
    if url_final.startswith("postgresql://"):
      url_final = url_final.replace(
        "postgresql://", "postgresql+psycopg2://", 1
      )
    self._engine: Engine = create_engine(url_final)
    self._fabrica_sesiones = sessionmaker(bind=self._engine)

  @property
  def engine(self) -> Engine:
    return self._engine

  def crear_tablas(self) -> None:
    """Crea las tablas definidas en los modelos si no existen."""
    import book_manager.models.models  # noqa: F401

    Base.metadata.create_all(self._engine)
