"""Conexión a la base de datos del sistema Book Manager."""
from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()

RUTA_DB: str = os.path.join(
  os.path.dirname(os.path.abspath(__file__)), "book_manager.db"
)


class ConexionDB:
  """Administra el motor, las tablas y las sesiones de SQLAlchemy."""

  def __init__(self, url: str = f"sqlite:///{RUTA_DB}") -> None:
    self._engine: Engine = create_engine(url)
    event.listen(self._engine, "connect", self._activar_claves)
    self._fabrica_sesiones = sessionmaker(bind=self._engine)

  @staticmethod
  def _activar_claves(conexion_dbapi: Any, registro: Any) -> None:
    """Activa el control de claves foráneas en SQLite."""
    cursor = conexion_dbapi.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

  @property
  def engine(self) -> Engine:
    return self._engine

  def crear_tablas(self) -> None:
    """Crea las tablas definidas en los modelos si no existen."""
    Base.metadata.create_all(self._engine)
