"""Modelos ORM (tablas) del sistema Book Manager."""
from __future__ import annotations

from sqlalchemy import (
  Column, Float, ForeignKey, Integer, String, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from book_manager.database.connection import Base


class GeneroModel(Base):
  """Tabla de géneros literarios."""

  __tablename__ = "generos"

  id = Column(Integer, primary_key=True, autoincrement=True)
  nombre = Column(String(100), nullable=False, unique=True)

  libros = relationship("LibroModel", back_populates="genero")


class EditorialModel(Base):
  """Tabla de editoriales proveedoras."""

  __tablename__ = "editoriales"

  id = Column(Integer, primary_key=True, autoincrement=True)
  nombre = Column(String(100), nullable=False, unique=True)
  pais = Column(String(100), nullable=False)

  libros = relationship("LibroModel", back_populates="editorial")


class MonedaModel(Base):
  """Tabla de monedas en las que se expresan los precios."""

  __tablename__ = "monedas"

  id = Column(Integer, primary_key=True, autoincrement=True)
  codigo = Column(String(3), nullable=False, unique=True)
  nombre = Column(String(100), nullable=False)

  precios = relationship("PrecioModel", back_populates="moneda")


class TipoCotizacionModel(Base):
  """Tabla de tipos de cotización del dólar."""

  __tablename__ = "tipos_cotizacion"

  id = Column(Integer, primary_key=True, autoincrement=True)
  nombre = Column(String(100), nullable=False, unique=True)

  cotizaciones = relationship(
    "CotizacionDolarModel", back_populates="tipo"
  )


class LibroModel(Base):
  """Tabla de libros del catálogo."""

  __tablename__ = "libros"

  id = Column(Integer, primary_key=True, autoincrement=True)
  isbn = Column(String(30), nullable=False, unique=True)
  titulo = Column(String(200), nullable=False)
  autor = Column(String(150), nullable=False)
  editorial_id = Column(
    Integer, ForeignKey("editoriales.id"), nullable=False
  )
  genero_id = Column(
    Integer, ForeignKey("generos.id"), nullable=False
  )

  editorial = relationship("EditorialModel", back_populates="libros")
  genero = relationship("GeneroModel", back_populates="libros")
  precios = relationship(
    "PrecioModel",
    back_populates="libro",
    cascade="all, delete-orphan",
  )
  stock = relationship(
    "StockModel",
    back_populates="libro",
    cascade="all, delete-orphan",
    uselist=False,
  )


class PrecioModel(Base):
  """Tabla de precios de un libro en cada moneda."""

  __tablename__ = "precios"
  __table_args__ = (
    UniqueConstraint("libro_id", "moneda_id", name="uq_libro_moneda"),
  )

  id = Column(Integer, primary_key=True, autoincrement=True)
  libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
  moneda_id = Column(
    Integer, ForeignKey("monedas.id"), nullable=False
  )
  monto = Column(Float, nullable=False)

  libro = relationship("LibroModel", back_populates="precios")
  moneda = relationship("MonedaModel", back_populates="precios")


class StockModel(Base):
  """Tabla de existencias de cada libro."""

  __tablename__ = "stocks"

  id = Column(Integer, primary_key=True, autoincrement=True)
  libro_id = Column(
    Integer, ForeignKey("libros.id"), nullable=False, unique=True
  )
  cantidad = Column(Integer, nullable=False, default=0)

  libro = relationship("LibroModel", back_populates="stock")


class CotizacionDolarModel(Base):
  """Tabla del histórico de cotizaciones del dólar."""

  __tablename__ = "cotizaciones"
  __table_args__ = (
    UniqueConstraint("tipo_id", "fecha", name="uq_tipo_fecha"),
  )

  id = Column(Integer, primary_key=True, autoincrement=True)
  tipo_id = Column(
    Integer, ForeignKey("tipos_cotizacion.id"), nullable=False
  )
  fecha = Column(String(10), nullable=False)
  valor_compra = Column(Float, nullable=False)
  valor_venta = Column(Float, nullable=False)

  tipo = relationship("TipoCotizacionModel", back_populates="cotizaciones")
