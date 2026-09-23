"""Entidades del dominio del sistema Book Manager."""
from __future__ import annotations

import abc
from typing import Optional


class EntidadBase(abc.ABC):
  """Clase base abstracta para toda entidad del sistema."""

  def __init__(self, id: Optional[int] = None) -> None:
    self._id = id

  @property
  def id(self) -> Optional[int]:
    return self._id

  @id.setter
  def id(self, valor: int) -> None:
    self._id = valor


class Genero(EntidadBase):
  """Categoría literaria a la que pertenece un libro."""

  def __init__(
    self, nombre: str, id: Optional[int] = None
  ) -> None:
    super().__init__(id)
    self._nombre = nombre

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, valor: str) -> None:
    self._nombre = valor

  def __repr__(self) -> str:
    return f"Genero(id={self.id}, nombre={self.nombre!r})"


class Editorial(EntidadBase):
  """Proveedor/distribuidora que provee libros a la librería."""

  def __init__(
    self, nombre: str, pais: str, id: Optional[int] = None
  ) -> None:
    super().__init__(id)
    self._nombre = nombre
    self._pais = pais

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, valor: str) -> None:
    self._nombre = valor

  @property
  def pais(self) -> str:
    return self._pais

  @pais.setter
  def pais(self, valor: str) -> None:
    self._pais = valor

  def __repr__(self) -> str:
    return (
      f"Editorial(id={self.id}, nombre={self.nombre!r}, "
      f"pais={self.pais!r})"
    )


class Moneda(EntidadBase):
  """Moneda en la que se puede expresar un precio."""

  def __init__(
    self, codigo: str, nombre: str, id: Optional[int] = None
  ) -> None:
    super().__init__(id)
    self._codigo = codigo.upper()
    self._nombre = nombre

  @property
  def codigo(self) -> str:
    return self._codigo

  @codigo.setter
  def codigo(self, valor: str) -> None:
    self._codigo = valor.upper()

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, valor: str) -> None:
    self._nombre = valor

  def __repr__(self) -> str:
    return f"Moneda(id={self.id}, codigo={self.codigo!r})"


class TipoCotizacion(EntidadBase):
  """Tipo de cotización del dólar (Oficial, Blue, MEP)."""

  def __init__(
    self, nombre: str, id: Optional[int] = None
  ) -> None:
    super().__init__(id)
    self._nombre = nombre

  @property
  def nombre(self) -> str:
    return self._nombre

  @nombre.setter
  def nombre(self, valor: str) -> None:
    self._nombre = valor

  def __repr__(self) -> str:
    return f"TipoCotizacion(id={self.id}, nombre={self.nombre!r})"


class Libro(EntidadBase):
  """Título del catálogo de la librería."""

  def __init__(
    self,
    isbn: str,
    titulo: str,
    autor: str,
    editorial: Editorial,
    genero: Genero,
    id: Optional[int] = None,
  ) -> None:
    super().__init__(id)
    self._isbn = isbn
    self._titulo = titulo
    self._autor = autor
    self._editorial = editorial
    self._genero = genero

  @property
  def isbn(self) -> str:
    return self._isbn

  @isbn.setter
  def isbn(self, valor: str) -> None:
    self._isbn = valor

  @property
  def titulo(self) -> str:
    return self._titulo

  @titulo.setter
  def titulo(self, valor: str) -> None:
    self._titulo = valor

  @property
  def autor(self) -> str:
    return self._autor

  @autor.setter
  def autor(self, valor: str) -> None:
    self._autor = valor

  @property
  def editorial(self) -> Editorial:
    return self._editorial

  @editorial.setter
  def editorial(self, valor: Editorial) -> None:
    self._editorial = valor

  @property
  def genero(self) -> Genero:
    return self._genero

  @genero.setter
  def genero(self, valor: Genero) -> None:
    self._genero = valor

  def __repr__(self) -> str:
    return (
      f"Libro(id={self.id}, isbn={self.isbn!r}, "
      f"titulo={self.titulo!r})"
    )


class Precio(EntidadBase):
  """Valor monetario de un libro en una moneda determinada."""

  def __init__(
    self,
    libro: Libro,
    moneda: Moneda,
    monto: float,
    id: Optional[int] = None,
  ) -> None:
    super().__init__(id)
    self._libro = libro
    self._moneda = moneda
    self.monto = monto

  @property
  def libro(self) -> Libro:
    return self._libro

  @libro.setter
  def libro(self, valor: Libro) -> None:
    self._libro = valor

  @property
  def moneda(self) -> Moneda:
    return self._moneda

  @moneda.setter
  def moneda(self, valor: Moneda) -> None:
    self._moneda = valor

  @property
  def monto(self) -> float:
    return self._monto

  @monto.setter
  def monto(self, valor: float) -> None:
    if valor < 0:
      raise ValueError("El monto no puede ser negativo.")
    self._monto = valor

  def __repr__(self) -> str:
    return (
      f"Precio(id={self.id}, libro={self.libro.titulo!r}, "
      f"monto={self.monto} {self.moneda.codigo})"
    )


class Stock(EntidadBase):
  """Cantidad disponible de un libro en inventario."""

  def __init__(
    self, libro: Libro, cantidad: int, id: Optional[int] = None
  ) -> None:
    super().__init__(id)
    self._libro = libro
    self.cantidad = cantidad

  @property
  def libro(self) -> Libro:
    return self._libro

  @libro.setter
  def libro(self, valor: Libro) -> None:
    self._libro = valor

  @property
  def cantidad(self) -> int:
    return self._cantidad

  @cantidad.setter
  def cantidad(self, valor: int) -> None:
    if valor < 0:
      raise ValueError("La cantidad no puede ser negativa.")
    self._cantidad = valor

  def __repr__(self) -> str:
    return (
      f"Stock(id={self.id}, libro={self.libro.titulo!r}, "
      f"cantidad={self.cantidad})"
    )


class CotizacionDolar(EntidadBase):
  """Registro histórico de cotización del dólar."""

  def __init__(
    self,
    tipo: TipoCotizacion,
    fecha: str,
    valor_compra: float,
    valor_venta: float,
    id: Optional[int] = None,
  ) -> None:
    super().__init__(id)
    self._tipo = tipo
    self._fecha = fecha
    self._valor_compra = valor_compra
    self._valor_venta = valor_venta

  @property
  def tipo(self) -> TipoCotizacion:
    return self._tipo

  @tipo.setter
  def tipo(self, valor: TipoCotizacion) -> None:
    self._tipo = valor

  @property
  def fecha(self) -> str:
    return self._fecha

  @fecha.setter
  def fecha(self, valor: str) -> None:
    self._fecha = valor

  @property
  def valor_compra(self) -> float:
    return self._valor_compra

  @valor_compra.setter
  def valor_compra(self, valor: float) -> None:
    self._valor_compra = valor

  @property
  def valor_venta(self) -> float:
    return self._valor_venta

  @valor_venta.setter
  def valor_venta(self, valor: float) -> None:
    self._valor_venta = valor

  def __repr__(self) -> str:
    return (
      f"CotizacionDolar(tipo={self.tipo.nombre!r}, "
      f"fecha={self.fecha!r}, venta={self.valor_venta})"
    )
