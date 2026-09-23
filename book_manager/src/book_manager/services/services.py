"""Servicios de lógica de negocio para Book Manager."""
from __future__ import annotations

import csv
import json
import os
import urllib.request
from datetime import date
from typing import Dict, List, Optional

from book_manager.entities.entities import (
  CotizacionDolar,
  Editorial,
  Genero,
  Libro,
  Moneda,
  Precio,
  Stock,
  TipoCotizacion,
)
from book_manager.repositories.repositories import (
  RepositorioCotizacionDolar,
  RepositorioEditorial,
  RepositorioGenero,
  RepositorioLibro,
  RepositorioMoneda,
  RepositorioPrecio,
  RepositorioStock,
  RepositorioTipoCotizacion,
)

URL_API_DOLAR: str = "https://dolarapi.com/v1/dolares"
RUTA_COMPETENCIA: str = os.path.join(
  os.path.dirname(__file__),
  "..", "migrations", "csv", "competencia.csv",
)


class ServicioCotizacion:
  """Obtiene y persiste cotizaciones del dólar en tiempo real."""

  def __init__(
    self,
    repo_cotizacion: RepositorioCotizacionDolar,
    repo_tipo: RepositorioTipoCotizacion,
  ) -> None:
    self._repo_cotizacion = repo_cotizacion
    self._repo_tipo = repo_tipo

  def obtener_cotizaciones_actuales(self) -> List[Dict]:
    """Consulta la API pública y retorna las cotizaciones vigentes."""
    try:
      with urllib.request.urlopen(
        URL_API_DOLAR, timeout=10
      ) as respuesta:
        return json.loads(respuesta.read())
    except Exception as error:
      print(f"No se pudo consultar la cotización: {error}")
      return []

  def actualizar_cotizaciones(self) -> List[CotizacionDolar]:
    """Actualiza el histórico de cotizaciones desde la API."""
    datos: List[Dict] = self.obtener_cotizaciones_actuales()
    hoy: str = date.today().isoformat()
    actualizadas: List[CotizacionDolar] = []

    for item in datos:
      nombre_tipo: str = str(item.get("nombre", "Desconocido"))
      tipo: TipoCotizacion = self._buscar_o_crear_tipo(
        nombre_tipo
      )
      existente = self._repo_cotizacion.leer_por_tipo_y_fecha(
        tipo.id, hoy
      )
      if existente:
        continue
      cotizacion: CotizacionDolar = CotizacionDolar(
        tipo=tipo,
        fecha=hoy,
        valor_compra=float(item.get("compra", 0.0) or 0.0),
        valor_venta=float(item.get("venta", 0.0) or 0.0),
      )
      self._repo_cotizacion.crear(cotizacion)
      actualizadas.append(cotizacion)

    return actualizadas

  def _buscar_o_crear_tipo(self, nombre: str) -> TipoCotizacion:
    for tipo in self._repo_tipo.leer_todos():
      if tipo.nombre.lower() == nombre.lower():
        return tipo
    return self._repo_tipo.crear(TipoCotizacion(nombre=nombre))

  def obtener_ultima_cotizacion(
    self, tipo_id: int
  ) -> Optional[CotizacionDolar]:
    """Retorna la cotización más reciente para un tipo dado."""
    historico: List[CotizacionDolar] = (
      self._repo_cotizacion.leer_historico_por_tipo(tipo_id)
    )
    if not historico:
      return None
    return max(historico, key=lambda c: c.fecha)


class ServicioPrecio:
  """Gestiona la conversión y consulta de precios de libros."""

  def __init__(
    self,
    repo_precio: RepositorioPrecio,
    repo_moneda: RepositorioMoneda,
    servicio_cotizacion: ServicioCotizacion,
  ) -> None:
    self._repo_precio = repo_precio
    self._repo_moneda = repo_moneda
    self._servicio_cotizacion = servicio_cotizacion

  def convertir_a_usd(
    self, monto_ars: float, tipo_cotizacion_id: int
  ) -> float:
    """Convierte un monto en ARS a USD según la cotización."""
    cotizacion: Optional[CotizacionDolar] = (
      self._servicio_cotizacion.obtener_ultima_cotizacion(
        tipo_cotizacion_id
      )
    )
    if cotizacion is None or cotizacion.valor_venta == 0:
      raise ValueError("No hay cotización disponible.")
    return round(monto_ars / cotizacion.valor_venta, 2)

  def precios_de_libro(self, libro_id: int) -> List[Precio]:
    """Retorna todos los precios registrados para un libro."""
    return [
      p for p in self._repo_precio.leer_todos()
      if p.libro.id == libro_id
    ]


class ServicioStock:
  """Gestiona el control de stock de libros."""

  def __init__(self, repo_stock: RepositorioStock) -> None:
    self._repo_stock = repo_stock

  def ingresar(self, libro_id: int, cantidad: int) -> Stock:
    """Incrementa el stock de un libro."""
    stock: Optional[Stock] = self._repo_stock.leer_por_libro(
      libro_id
    )
    if stock is None:
      raise ValueError(
        f"No existe stock para el libro id={libro_id}."
      )
    stock.cantidad = stock.cantidad + cantidad
    return self._repo_stock.actualizar(stock)

  def egresar(self, libro_id: int, cantidad: int) -> Stock:
    """Reduce el stock de un libro validando disponibilidad."""
    stock: Optional[Stock] = self._repo_stock.leer_por_libro(
      libro_id
    )
    if stock is None:
      raise ValueError(
        f"No existe stock para el libro id={libro_id}."
      )
    if stock.cantidad < cantidad:
      raise ValueError("Stock insuficiente para el egreso.")
    stock.cantidad = stock.cantidad - cantidad
    return self._repo_stock.actualizar(stock)


class ServicioLibro:
  """Gestiona operaciones de alto nivel sobre libros."""

  def __init__(
    self,
    repo_libro: RepositorioLibro,
    repo_precio: RepositorioPrecio,
    repo_stock: RepositorioStock,
  ) -> None:
    self._repo_libro = repo_libro
    self._repo_precio = repo_precio
    self._repo_stock = repo_stock

  def registrar_libro(
    self,
    isbn: str,
    titulo: str,
    autor: str,
    editorial: Editorial,
    genero: Genero,
    precio_ars: float,
    moneda_ars: Moneda,
    cantidad_inicial: int,
  ) -> Libro:
    """Crea un libro con su precio inicial y stock asociado."""
    libro: Libro = self._repo_libro.crear(
      Libro(
        isbn=isbn,
        titulo=titulo,
        autor=autor,
        editorial=editorial,
        genero=genero,
      )
    )
    self._repo_precio.crear(
      Precio(libro=libro, moneda=moneda_ars, monto=precio_ars)
    )
    self._repo_stock.crear(
      Stock(libro=libro, cantidad=cantidad_inicial)
    )
    return libro

  def buscar_por_genero(self, genero_id: int) -> List[Libro]:
    """Retorna todos los libros de un género dado."""
    return [
      l for l in self._repo_libro.leer_todos()
      if l.genero.id == genero_id
    ]


class ServicioComparacionCompetencia:
  """Compara precios propios contra precios de referencia."""

  def __init__(self, repo_libro: RepositorioLibro) -> None:
    self._repo_libro = repo_libro

  def _cargar_precios_competencia(self) -> Dict[str, float]:
    precios: Dict[str, float] = {}
    if not os.path.exists(RUTA_COMPETENCIA):
      return precios
    with open(
      RUTA_COMPETENCIA, "r", newline="", encoding="utf-8"
    ) as f:
      for fila in csv.DictReader(f):
        precios[fila["isbn"]] = float(fila["precio_ars"])
    return precios

  def comparar(self, isbn: str, precio_propio: float) -> str:
    """Compara un precio propio contra el de la competencia."""
    precios: Dict[str, float] = (
      self._cargar_precios_competencia()
    )
    if isbn not in precios:
      return "Sin datos de competencia."
    precio_comp: float = precios[isbn]
    if precio_propio < precio_comp:
      return f"Más barato que Cúspide (${precio_comp})."
    if precio_propio > precio_comp:
      return f"Más caro que Cúspide (${precio_comp})."
    return "Mismo precio que Cúspide."


class ServicioReportes:
  """Genera reportes agregados del sistema."""

  def __init__(
    self,
    repo_libro: RepositorioLibro,
    repo_stock: RepositorioStock,
    servicio_precio: ServicioPrecio,
  ) -> None:
    self._repo_libro = repo_libro
    self._repo_stock = repo_stock
    self._servicio_precio = servicio_precio

  def libros_con_bajo_stock(self, umbral: int = 5) -> List[Stock]:
    """Retorna los libros cuyo stock está por debajo del umbral."""
    return [
      s for s in self._repo_stock.leer_todos()
      if s.cantidad < umbral
    ]

  def catalogo_completo(self) -> List[Dict[str, object]]:
    """Retorna un resumen de cada libro con precio y stock."""
    resumen: List[Dict[str, object]] = []
    for libro in self._repo_libro.leer_todos():
      precios: List[Precio] = (
        self._servicio_precio.precios_de_libro(libro.id)
      )
      stock: Optional[Stock] = (
        self._repo_stock.leer_por_libro(libro.id)
      )
      resumen.append({
        "libro": libro,
        "precios": precios,
        "cantidad": stock.cantidad if stock else 0,
      })
    return resumen
