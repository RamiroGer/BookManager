"""Repositorios para persistencia de entidades en archivos CSV."""
from __future__ import annotations

import abc
import csv
import os
from typing import Dict, Generic, List, Optional, TypeVar

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

T = TypeVar("T", bound=EntidadBase)

RUTA_CSV: str = os.path.join(
  os.path.dirname(__file__), "..", "migrations", "csv"
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


class RepositorioCSVBase(IRepositorio[T], abc.ABC):
  """Repositorio genérico con persistencia en archivo CSV."""

  def __init__(self, nombre_archivo: str) -> None:
    self._ruta: str = os.path.join(RUTA_CSV, nombre_archivo)
    self._datos: Dict[int, T] = {}
    self._siguiente_id: int = 1
    self._cargar()

  @abc.abstractmethod
  def _encabezados(self) -> List[str]:
    """Retorna los encabezados de columnas del CSV."""

  @abc.abstractmethod
  def _a_fila(self, entidad: T) -> List[str]:
    """Convierte una entidad en una fila de valores CSV."""

  @abc.abstractmethod
  def _desde_fila(self, fila: Dict[str, str]) -> T:
    """Convierte una fila de CSV en una entidad."""

  def _cargar(self) -> None:
    if not os.path.exists(self._ruta):
      return
    with open(self._ruta, "r", newline="", encoding="utf-8") as f:
      lector = csv.DictReader(f)
      for fila in lector:
        entidad: T = self._desde_fila(fila)
        self._datos[entidad.id] = entidad
        self._siguiente_id = max(
          self._siguiente_id, entidad.id + 1
        )

  def _guardar(self) -> None:
    os.makedirs(os.path.dirname(self._ruta), exist_ok=True)
    with open(self._ruta, "w", newline="", encoding="utf-8") as f:
      escritor = csv.writer(f)
      escritor.writerow(self._encabezados())
      for entidad in self._datos.values():
        escritor.writerow(self._a_fila(entidad))

  def crear(self, entidad: T) -> T:
    entidad.id = self._siguiente_id
    self._siguiente_id += 1
    self._datos[entidad.id] = entidad
    self._guardar()
    return entidad

  def leer_por_id(self, id: int) -> Optional[T]:
    return self._datos.get(id)

  def leer_todos(self) -> List[T]:
    return list(self._datos.values())

  def actualizar(self, entidad: T) -> T:
    if entidad.id not in self._datos:
      raise ValueError(
        f"No se encontró la entidad con id={entidad.id}."
      )
    self._datos[entidad.id] = entidad
    self._guardar()
    return entidad

  def eliminar(self, id: int) -> bool:
    if id not in self._datos:
      return False
    del self._datos[id]
    self._guardar()
    return True


class RepositorioGenero(RepositorioCSVBase[Genero]):
  """Repositorio CSV para la entidad Genero."""

  def __init__(self) -> None:
    super().__init__("generos.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "nombre"]

  def _a_fila(self, entidad: Genero) -> List[str]:
    return [str(entidad.id), entidad.nombre]

  def _desde_fila(self, fila: Dict[str, str]) -> Genero:
    return Genero(nombre=fila["nombre"], id=int(fila["id"]))


class RepositorioEditorial(RepositorioCSVBase[Editorial]):
  """Repositorio CSV para la entidad Editorial."""

  def __init__(self) -> None:
    super().__init__("editoriales.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "nombre", "pais"]

  def _a_fila(self, entidad: Editorial) -> List[str]:
    return [str(entidad.id), entidad.nombre, entidad.pais]

  def _desde_fila(self, fila: Dict[str, str]) -> Editorial:
    return Editorial(
      nombre=fila["nombre"],
      pais=fila["pais"],
      id=int(fila["id"]),
    )


class RepositorioMoneda(RepositorioCSVBase[Moneda]):
  """Repositorio CSV para la entidad Moneda."""

  def __init__(self) -> None:
    super().__init__("monedas.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "codigo", "nombre"]

  def _a_fila(self, entidad: Moneda) -> List[str]:
    return [str(entidad.id), entidad.codigo, entidad.nombre]

  def _desde_fila(self, fila: Dict[str, str]) -> Moneda:
    return Moneda(
      codigo=fila["codigo"],
      nombre=fila["nombre"],
      id=int(fila["id"]),
    )


class RepositorioTipoCotizacion(
  RepositorioCSVBase[TipoCotizacion]
):
  """Repositorio CSV para la entidad TipoCotizacion."""

  def __init__(self) -> None:
    super().__init__("tipos_cotizacion.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "nombre"]

  def _a_fila(self, entidad: TipoCotizacion) -> List[str]:
    return [str(entidad.id), entidad.nombre]

  def _desde_fila(
    self, fila: Dict[str, str]
  ) -> TipoCotizacion:
    return TipoCotizacion(
      nombre=fila["nombre"], id=int(fila["id"])
    )


class RepositorioLibro(RepositorioCSVBase[Libro]):
  """Repositorio CSV para la entidad Libro."""

  def __init__(
    self,
    repo_editorial: RepositorioEditorial,
    repo_genero: RepositorioGenero,
  ) -> None:
    self._repo_editorial = repo_editorial
    self._repo_genero = repo_genero
    super().__init__("libros.csv")

  def _encabezados(self) -> List[str]:
    return [
      "id", "isbn", "titulo", "autor",
      "editorial_id", "genero_id",
    ]

  def _a_fila(self, entidad: Libro) -> List[str]:
    return [
      str(entidad.id),
      entidad.isbn,
      entidad.titulo,
      entidad.autor,
      str(entidad.editorial.id),
      str(entidad.genero.id),
    ]

  def _desde_fila(self, fila: Dict[str, str]) -> Libro:
    editorial: Optional[Editorial] = (
      self._repo_editorial.leer_por_id(
        int(fila["editorial_id"])
      )
    )
    genero: Optional[Genero] = (
      self._repo_genero.leer_por_id(int(fila["genero_id"]))
    )
    return Libro(
      isbn=fila["isbn"],
      titulo=fila["titulo"],
      autor=fila["autor"],
      editorial=editorial,
      genero=genero,
      id=int(fila["id"]),
    )


class RepositorioPrecio(RepositorioCSVBase[Precio]):
  """Repositorio CSV para la entidad Precio."""

  def __init__(
    self,
    repo_libro: RepositorioLibro,
    repo_moneda: RepositorioMoneda,
  ) -> None:
    self._repo_libro = repo_libro
    self._repo_moneda = repo_moneda
    super().__init__("precios.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "libro_id", "moneda_id", "monto"]

  def _a_fila(self, entidad: Precio) -> List[str]:
    return [
      str(entidad.id),
      str(entidad.libro.id),
      str(entidad.moneda.id),
      str(entidad.monto),
    ]

  def _desde_fila(self, fila: Dict[str, str]) -> Precio:
    libro: Optional[Libro] = (
      self._repo_libro.leer_por_id(int(fila["libro_id"]))
    )
    moneda: Optional[Moneda] = (
      self._repo_moneda.leer_por_id(int(fila["moneda_id"]))
    )
    return Precio(
      libro=libro,
      moneda=moneda,
      monto=float(fila["monto"]),
      id=int(fila["id"]),
    )


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


class RepositorioStock(
  RepositorioCSVBase[Stock], IRepositorioStock
):
  """Repositorio CSV para la entidad Stock."""

  def __init__(self, repo_libro: RepositorioLibro) -> None:
    self._repo_libro = repo_libro
    super().__init__("stocks.csv")

  def _encabezados(self) -> List[str]:
    return ["id", "libro_id", "cantidad"]

  def _a_fila(self, entidad: Stock) -> List[str]:
    return [
      str(entidad.id),
      str(entidad.libro.id),
      str(entidad.cantidad),
    ]

  def _desde_fila(self, fila: Dict[str, str]) -> Stock:
    libro: Optional[Libro] = (
      self._repo_libro.leer_por_id(int(fila["libro_id"]))
    )
    return Stock(
      libro=libro,
      cantidad=int(fila["cantidad"]),
      id=int(fila["id"]),
    )

  def leer_por_libro(self, libro_id: int) -> Optional[Stock]:
    for stock in self._datos.values():
      if stock.libro.id == libro_id:
        return stock
    return None

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
  RepositorioCSVBase[CotizacionDolar],
  IRepositorioCotizacionDolar,
):
  """Repositorio CSV para la entidad CotizacionDolar."""

  def __init__(
    self, repo_tipo: RepositorioTipoCotizacion
  ) -> None:
    self._repo_tipo = repo_tipo
    super().__init__("cotizaciones.csv")

  def _encabezados(self) -> List[str]:
    return [
      "id", "tipo_id", "fecha",
      "valor_compra", "valor_venta",
    ]

  def _a_fila(self, entidad: CotizacionDolar) -> List[str]:
    return [
      str(entidad.id),
      str(entidad.tipo.id),
      entidad.fecha,
      str(entidad.valor_compra),
      str(entidad.valor_venta),
    ]

  def _desde_fila(
    self, fila: Dict[str, str]
  ) -> CotizacionDolar:
    tipo: Optional[TipoCotizacion] = (
      self._repo_tipo.leer_por_id(int(fila["tipo_id"]))
    )
    return CotizacionDolar(
      tipo=tipo,
      fecha=fila["fecha"],
      valor_compra=float(fila["valor_compra"]),
      valor_venta=float(fila["valor_venta"]),
      id=int(fila["id"]),
    )

  def leer_por_tipo_y_fecha(
    self, tipo_id: int, fecha: str
  ) -> Optional[CotizacionDolar]:
    for cot in self._datos.values():
      if cot.tipo.id == tipo_id and cot.fecha == fecha:
        return cot
    return None

  def leer_historico_por_tipo(
    self, tipo_id: int
  ) -> List[CotizacionDolar]:
    return [
      cot for cot in self._datos.values()
      if cot.tipo.id == tipo_id
    ]

  def eliminar(self, tipo_id: int, fecha: str) -> bool:
    cot: Optional[CotizacionDolar] = (
      self.leer_por_tipo_y_fecha(tipo_id, fecha)
    )
    if cot is None:
      return False
    return super().eliminar(cot.id)
