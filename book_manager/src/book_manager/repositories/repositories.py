"""Repositorios para persistencia de entidades en base de datos."""
from __future__ import annotations

import abc
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from book_manager.database.connection import ConexionDB
from book_manager.entities.entities import (
  CotizacionDolar,
  Editorial,
  EntidadBase,
  Genero,
  Libro,
  Moneda,
  Precio,
  Stock,
  TipoCotizacion,
)
from book_manager.models.models import (
  CotizacionDolarModel,
  EditorialModel,
  GeneroModel,
  LibroModel,
  MonedaModel,
  PrecioModel,
  StockModel,
  TipoCotizacionModel,
)

T = TypeVar("T", bound=EntidadBase)


def _genero(m: GeneroModel) -> Genero:
  """Convierte un modelo de género en entidad."""
  return Genero(nombre=m.nombre, id=m.id)


def _editorial(m: EditorialModel) -> Editorial:
  """Convierte un modelo de editorial en entidad."""
  return Editorial(nombre=m.nombre, pais=m.pais, id=m.id)


def _moneda(m: MonedaModel) -> Moneda:
  """Convierte un modelo de moneda en entidad."""
  return Moneda(codigo=m.codigo, nombre=m.nombre, id=m.id)


def _tipo(m: TipoCotizacionModel) -> TipoCotizacion:
  """Convierte un modelo de tipo de cotización en entidad."""
  return TipoCotizacion(nombre=m.nombre, id=m.id)


def _libro(m: LibroModel) -> Libro:
  """Convierte un modelo de libro en entidad."""
  return Libro(
    isbn=m.isbn,
    titulo=m.titulo,
    autor=m.autor,
    editorial=_editorial(m.editorial),
    genero=_genero(m.genero),
    id=m.id,
  )


class IRepositorio(abc.ABC, Generic[T]):
  """Interfaz para repositorios con operaciones CRUD básicas."""

  @abc.abstractmethod
  def crear(self, entidad: T) -> T:
    """Crea una nueva entidad en el repositorio."""

  @abc.abstractmethod
  def leer_por_id(self, id: int) -> Optional[T]:
    """Lee una entidad por su ID."""

  @abc.abstractmethod
  def leer_todos(self) -> List[T]:
    """Lee todas las entidades del repositorio."""

  @abc.abstractmethod
  def actualizar(self, entidad: T) -> T:
    """Actualiza una entidad existente."""

  @abc.abstractmethod
  def eliminar(self, id: int) -> bool:
    """Elimina una entidad por su ID."""


class RepositorioDBBase(IRepositorio[T], abc.ABC):
  """Repositorio genérico con persistencia en base de datos."""

  def __init__(self, conexion: ConexionDB, modelo: Type[Any]) -> None:
    self._conexion = conexion
    self._modelo = modelo

  @abc.abstractmethod
  def _a_entidad(self, modelo: Any) -> T:
    """Convierte un modelo ORM en una entidad del dominio."""

  @abc.abstractmethod
  def _volcar(self, modelo: Any, entidad: T) -> None:
    """Copia los datos de la entidad hacia el modelo ORM."""

  def _guardar(self, sesion: Session, modelo: Any) -> None:
    """Persiste el modelo y traduce los errores de integridad."""
    try:
      sesion.add(modelo)
      sesion.flush()
    except IntegrityError as error:
      sesion.rollback()
      raise ValueError(
        "Dato duplicado o referencia inexistente."
      ) from error

  def crear(self, entidad: T) -> T:
    with self._conexion.transaccion() as sesion:
      modelo = self._modelo()
      self._volcar(modelo, entidad)
      self._guardar(sesion, modelo)
      entidad.id = modelo.id
    return entidad

  def leer_por_id(self, id: int) -> Optional[T]:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.get(self._modelo, id)
      return None if modelo is None else self._a_entidad(modelo)

  def leer_todos(self) -> List[T]:
    with self._conexion.transaccion() as sesion:
      modelos = sesion.query(self._modelo).order_by(
        self._modelo.id
      ).all()
      return [self._a_entidad(m) for m in modelos]

  def actualizar(self, entidad: T) -> T:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.get(self._modelo, entidad.id)
      if modelo is None:
        raise ValueError(
          f"No se encontró la entidad con id={entidad.id}."
        )
      self._volcar(modelo, entidad)
      self._guardar(sesion, modelo)
    return entidad

  def eliminar(self, id: int) -> bool:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.get(self._modelo, id)
      if modelo is None:
        return False
      try:
        sesion.delete(modelo)
        sesion.flush()
      except IntegrityError as error:
        sesion.rollback()
        raise ValueError(
          "No se puede eliminar: tiene registros asociados."
        ) from error
      return True


class RepositorioGenero(RepositorioDBBase[Genero]):
  """Repositorio para la entidad Genero."""

  def __init__(self, conexion: ConexionDB) -> None:
    super().__init__(conexion, GeneroModel)

  def _a_entidad(self, modelo: GeneroModel) -> Genero:
    return _genero(modelo)

  def _volcar(self, modelo: GeneroModel, entidad: Genero) -> None:
    modelo.nombre = entidad.nombre


class RepositorioEditorial(RepositorioDBBase[Editorial]):
  """Repositorio para la entidad Editorial."""

  def __init__(self, conexion: ConexionDB) -> None:
    super().__init__(conexion, EditorialModel)

  def _a_entidad(self, modelo: EditorialModel) -> Editorial:
    return _editorial(modelo)

  def _volcar(
    self, modelo: EditorialModel, entidad: Editorial
  ) -> None:
    modelo.nombre = entidad.nombre
    modelo.pais = entidad.pais


class RepositorioMoneda(RepositorioDBBase[Moneda]):
  """Repositorio para la entidad Moneda."""

  def __init__(self, conexion: ConexionDB) -> None:
    super().__init__(conexion, MonedaModel)

  def _a_entidad(self, modelo: MonedaModel) -> Moneda:
    return _moneda(modelo)

  def _volcar(self, modelo: MonedaModel, entidad: Moneda) -> None:
    modelo.codigo = entidad.codigo
    modelo.nombre = entidad.nombre


class RepositorioTipoCotizacion(RepositorioDBBase[TipoCotizacion]):
  """Repositorio para la entidad TipoCotizacion."""

  def __init__(self, conexion: ConexionDB) -> None:
    super().__init__(conexion, TipoCotizacionModel)

  def _a_entidad(self, modelo: TipoCotizacionModel) -> TipoCotizacion:
    return _tipo(modelo)

  def _volcar(
    self, modelo: TipoCotizacionModel, entidad: TipoCotizacion
  ) -> None:
    modelo.nombre = entidad.nombre


class RepositorioLibro(RepositorioDBBase[Libro]):
  """Repositorio para la entidad Libro."""

  def __init__(self, conexion: ConexionDB) -> None:
    super().__init__(conexion, LibroModel)

  def _a_entidad(self, modelo: LibroModel) -> Libro:
    return _libro(modelo)

  def _volcar(self, modelo: LibroModel, entidad: Libro) -> None:
    modelo.isbn = entidad.isbn
    modelo.titulo = entidad.titulo
    modelo.autor = entidad.autor
    modelo.editorial_id = entidad.editorial.id
    modelo.genero_id = entidad.genero.id


class RepositorioPrecio(RepositorioDBBase[Precio]):
  """Repositorio para la entidad Precio."""

  def __init__(self, conexion: ConexionDB) -> None:
    super().__init__(conexion, PrecioModel)

  def _a_entidad(self, modelo: PrecioModel) -> Precio:
    return Precio(
      libro=_libro(modelo.libro),
      moneda=_moneda(modelo.moneda),
      monto=modelo.monto,
      id=modelo.id,
    )

  def _volcar(self, modelo: PrecioModel, entidad: Precio) -> None:
    modelo.libro_id = entidad.libro.id
    modelo.moneda_id = entidad.moneda.id
    modelo.monto = entidad.monto


class IRepositorioStock(abc.ABC):
  """Interfaz para repositorios del tipo Stock."""

  @abc.abstractmethod
  def crear(self, stock: Stock) -> Stock:
    """Crea un nuevo registro de stock."""

  @abc.abstractmethod
  def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
    """Lee un registro de stock por ID de libro."""

  @abc.abstractmethod
  def actualizar(self, stock: Stock) -> Stock:
    """Actualiza un registro de stock existente."""

  @abc.abstractmethod
  def eliminar(self, libro_id: int) -> bool:
    """Elimina un registro de stock por ID de libro."""


class RepositorioStock(RepositorioDBBase[Stock], IRepositorioStock):
  """Repositorio para la entidad Stock."""

  def __init__(self, conexion: ConexionDB) -> None:
    super().__init__(conexion, StockModel)

  def _a_entidad(self, modelo: StockModel) -> Stock:
    return Stock(
      libro=_libro(modelo.libro),
      cantidad=modelo.cantidad,
      id=modelo.id,
    )

  def _volcar(self, modelo: StockModel, entidad: Stock) -> None:
    modelo.libro_id = entidad.libro.id
    modelo.cantidad = entidad.cantidad

  def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.query(StockModel).filter_by(
        libro_id=libro_id
      ).first()
      return None if modelo is None else self._a_entidad(modelo)

  def eliminar(self, libro_id: int) -> bool:
    stock: Optional[Stock] = self.leer_por_libro(libro_id)
    if stock is None:
      return False
    return super().eliminar(stock.id)


class IRepositorioCotizacionDolar(abc.ABC):
  """Interfaz para repositorios del tipo CotizacionDolar."""

  @abc.abstractmethod
  def crear(
    self, cotizacion: CotizacionDolar
  ) -> CotizacionDolar:
    """Crea una nueva cotización de dólar."""

  @abc.abstractmethod
  def leer_por_tipo_y_fecha(
    self, tipo_id: int, fecha: str
  ) -> Optional[CotizacionDolar]:
    """Lee una cotización por tipo y fecha."""

  @abc.abstractmethod
  def leer_historico_por_tipo(
    self, tipo_id: int
  ) -> List[CotizacionDolar]:
    """Lee el histórico de cotizaciones para un tipo."""

  @abc.abstractmethod
  def actualizar(
    self, cotizacion: CotizacionDolar
  ) -> CotizacionDolar:
    """Actualiza una cotización existente."""

  @abc.abstractmethod
  def eliminar(self, tipo_id: int, fecha: str) -> bool:
    """Elimina una cotización por tipo y fecha."""


class RepositorioCotizacionDolar(
  RepositorioDBBase[CotizacionDolar], IRepositorioCotizacionDolar
):
  """Repositorio para la entidad CotizacionDolar."""

  def __init__(self, conexion: ConexionDB) -> None:
    super().__init__(conexion, CotizacionDolarModel)

  def _a_entidad(
    self, modelo: CotizacionDolarModel
  ) -> CotizacionDolar:
    return CotizacionDolar(
      tipo=_tipo(modelo.tipo),
      fecha=modelo.fecha,
      valor_compra=modelo.valor_compra,
      valor_venta=modelo.valor_venta,
      id=modelo.id,
    )

  def _volcar(
    self, modelo: CotizacionDolarModel, entidad: CotizacionDolar
  ) -> None:
    modelo.tipo_id = entidad.tipo.id
    modelo.fecha = entidad.fecha
    modelo.valor_compra = entidad.valor_compra
    modelo.valor_venta = entidad.valor_venta

  def leer_por_tipo_y_fecha(
    self, tipo_id: int, fecha: str
  ) -> Optional[CotizacionDolar]:
    with self._conexion.transaccion() as sesion:
      modelo = sesion.query(CotizacionDolarModel).filter_by(
        tipo_id=tipo_id, fecha=fecha
      ).first()
      return None if modelo is None else self._a_entidad(modelo)

  def leer_historico_por_tipo(
    self, tipo_id: int
  ) -> List[CotizacionDolar]:
    with self._conexion.transaccion() as sesion:
      modelos = sesion.query(CotizacionDolarModel).filter_by(
        tipo_id=tipo_id
      ).order_by(CotizacionDolarModel.fecha).all()
      return [self._a_entidad(m) for m in modelos]

  def eliminar(self, tipo_id: int, fecha: str) -> bool:
    cot: Optional[CotizacionDolar] = self.leer_por_tipo_y_fecha(
      tipo_id, fecha
    )
    if cot is None:
      return False
    return super().eliminar(cot.id)
