"""Servicios de lógica de negocio para Book Manager."""
from __future__ import annotations

import csv
import json
import os
import urllib.request
from datetime import date
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

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
  RepositorioLibro,
  RepositorioMoneda,
  RepositorioPrecio,
  RepositorioStock,
  RepositorioTipoCotizacion,
)

RUTA_BASE: str = os.path.join(
  os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."
)
RUTA_ENV: str = os.path.join(RUTA_BASE, ".env")
RUTA_EXPORTS: str = os.path.join(RUTA_BASE, "exports")

load_dotenv(RUTA_ENV)

NOMBRES_API: Dict[str, str] = {
  "Bolsa": "MEP",
  "Contado con liquidación": "CCL",
}


class ServicioCotizacionDolar:
  """Gestiona el registro de cotizaciones del dólar vía API."""

  def __init__(
    self,
    repo_cotizacion: RepositorioCotizacionDolar,
    repo_tipo: RepositorioTipoCotizacion,
  ) -> None:
    self._repo_cotizacion = repo_cotizacion
    self._repo_tipo = repo_tipo

  def _descargar_cotizaciones(self) -> List[Dict]:
    """Descarga el listado de cotizaciones desde la API."""
    url: Optional[str] = os.getenv("API_URL")
    if not url:
      raise ValueError("Falta la variable API_URL en el .env.")
    peticion = urllib.request.Request(
      url, headers={"User-Agent": "Mozilla/5.0"}
    )
    try:
      with urllib.request.urlopen(
        peticion, timeout=10
      ) as respuesta:
        return json.loads(respuesta.read())
    except (OSError, ValueError) as error:
      raise ConnectionError(
        f"No se pudo consultar la API: {error}"
      ) from error

  def _buscar_o_crear_tipo(self, nombre: str) -> TipoCotizacion:
    """Retorna el tipo con ese nombre, creándolo si no existe."""
    for tipo in self._repo_tipo.leer_todos():
      if tipo.nombre.lower() == nombre.lower():
        return tipo
    return self._repo_tipo.crear(TipoCotizacion(nombre=nombre))

  def obtener_cotizaciones(self) -> List[CotizacionDolar]:
    """Descarga y registra en la base las cotizaciones de la API."""
    registradas: List[CotizacionDolar] = []
    for item in self._descargar_cotizaciones():
      nombre_api: str = str(item.get("nombre", "")).strip()
      if not nombre_api:
        continue
      tipo: TipoCotizacion = self._buscar_o_crear_tipo(
        NOMBRES_API.get(nombre_api, nombre_api)
      )
      fecha: str = (
        str(item.get("fechaActualizacion") or "")[:10]
        or date.today().isoformat()
      )
      registradas.append(
        self.registrar_cotizacion(
          tipo.id,
          float(item.get("compra") or 0.0),
          float(item.get("venta") or 0.0),
          fecha,
        )
      )
    return registradas

  def registrar_cotizacion(
    self,
    tipo_id: int,
    valor_compra: float,
    valor_venta: float,
    fecha: Optional[str] = None,
  ) -> CotizacionDolar:
    """Registra la cotización de un tipo y fecha, o la actualiza."""
    tipo: Optional[TipoCotizacion] = self._repo_tipo.leer_por_id(
      tipo_id
    )
    if tipo is None:
      raise ValueError(f"No existe el tipo id={tipo_id}.")
    fecha_real: str = fecha or date.today().isoformat()
    existente: Optional[CotizacionDolar] = (
      self._repo_cotizacion.leer_por_tipo_y_fecha(
        tipo_id, fecha_real
      )
    )
    if existente is not None:
      existente.valor_compra = valor_compra
      existente.valor_venta = valor_venta
      return self._repo_cotizacion.actualizar(existente)
    return self._repo_cotizacion.crear(
      CotizacionDolar(
        tipo=tipo,
        fecha=fecha_real,
        valor_compra=valor_compra,
        valor_venta=valor_venta,
      )
    )

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
  """Gestiona los precios de libros en ARS y USD."""

  def __init__(
    self,
    repo_precio: RepositorioPrecio,
    repo_moneda: RepositorioMoneda,
    repo_libro: RepositorioLibro,
    servicio_cotizacion: ServicioCotizacionDolar,
  ) -> None:
    self._repo_precio = repo_precio
    self._repo_moneda = repo_moneda
    self._repo_libro = repo_libro
    self._servicio_cotizacion = servicio_cotizacion

  def precios_de_libro(self, libro_id: int) -> List[Precio]:
    """Retorna todos los precios registrados para un libro."""
    return [
      p for p in self._repo_precio.leer_todos()
      if p.libro.id == libro_id
    ]

  def precio_por_moneda(
    self, libro_id: int, codigo_moneda: str
  ) -> Optional[Precio]:
    """Retorna el precio de un libro en una moneda específica."""
    for precio in self.precios_de_libro(libro_id):
      if precio.moneda.codigo == codigo_moneda.upper():
        return precio
    return None

  def sugerir_precio_ars(
    self, libro_id: int, tipo_cotizacion_id: int
  ) -> float:
    """Sugiere el precio ARS según el precio USD y la cotización."""
    precio_usd: Optional[Precio] = self.precio_por_moneda(
      libro_id, "USD"
    )
    if precio_usd is None:
      raise ValueError("El libro no tiene precio en USD.")
    cotizacion: Optional[CotizacionDolar] = (
      self._servicio_cotizacion.obtener_ultima_cotizacion(
        tipo_cotizacion_id
      )
    )
    if cotizacion is None:
      raise ValueError("No hay cotización registrada.")
    return round(precio_usd.monto * cotizacion.valor_venta, 2)

  def comparar_ars_vs_sugerido(
    self, libro_id: int, tipo_cotizacion_id: int
  ) -> Tuple[float, float, float]:
    """Compara el precio ARS actual contra el sugerido por USD."""
    precio_ars: Optional[Precio] = self.precio_por_moneda(
      libro_id, "ARS"
    )
    if precio_ars is None:
      raise ValueError("El libro no tiene precio en ARS.")
    sugerido: float = self.sugerir_precio_ars(
      libro_id, tipo_cotizacion_id
    )
    diferencia: float = round(sugerido - precio_ars.monto, 2)
    return precio_ars.monto, sugerido, diferencia

  def aplicar_precio_ars(
    self, libro_id: int, monto_ars: float
  ) -> Precio:
    """Actualiza el precio en ARS vigente de un libro."""
    precio_ars: Optional[Precio] = self.precio_por_moneda(
      libro_id, "ARS"
    )
    if precio_ars is None:
      raise ValueError("El libro no tiene precio en ARS.")
    precio_ars.monto = monto_ars
    return self._repo_precio.actualizar(precio_ars)

  def lista_bimonetaria(
    self, codigo_otra: str
  ) -> List[Tuple[Libro, Optional[float], Optional[float]]]:
    """Lista cada libro con su precio en ARS y en otra moneda."""
    lista: List[Tuple[Libro, Optional[float], Optional[float]]] = []
    for libro in self._repo_libro.leer_todos():
      precio_ars: Optional[Precio] = self.precio_por_moneda(
        libro.id, "ARS"
      )
      precio_otra: Optional[Precio] = self.precio_por_moneda(
        libro.id, codigo_otra
      )
      lista.append((
        libro,
        precio_ars.monto if precio_ars else None,
        precio_otra.monto if precio_otra else None,
      ))
    return lista

  def exportar_precios_csv(
    self, carpeta: str = RUTA_EXPORTS
  ) -> str:
    """Exporta los precios de todas las monedas a un archivo CSV."""
    monedas: List[Moneda] = self._repo_moneda.leer_todos()
    os.makedirs(carpeta, exist_ok=True)
    ruta: str = os.path.join(carpeta, "precios.csv")
    with open(ruta, "w", newline="", encoding="utf-8") as f:
      escritor = csv.writer(f)
      escritor.writerow(
        ["isbn", "titulo"] + [m.codigo for m in monedas]
      )
      for libro in self._repo_libro.leer_todos():
        fila: List[str] = [libro.isbn, libro.titulo]
        for moneda in monedas:
          precio: Optional[Precio] = self.precio_por_moneda(
            libro.id, moneda.codigo
          )
          fila.append("" if precio is None else str(precio.monto))
        escritor.writerow(fila)
    return os.path.abspath(ruta)


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
    precio_usd: float,
    moneda_ars: Moneda,
    moneda_usd: Moneda,
    cantidad_inicial: int,
  ) -> Libro:
    """Crea un libro con precios en ARS y USD, y stock asociado."""
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
    self._repo_precio.crear(
      Precio(libro=libro, moneda=moneda_usd, monto=precio_usd)
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


# DESHABILITADO: la comparación con la competencia (Cúspide)
# implica técnicas de web scraping (Tema 9), que todavía no
# se vio en la cursada. Se deja comentado para uso futuro.
#
# class ServicioComparacionCompetencia:
#   """Compara precios propios (ARS y USD) contra la competencia."""
#
#   def __init__(self, repo_libro: RepositorioLibro) -> None:
#     self._repo_libro = repo_libro
#
#   def _cargar_precios_competencia(
#     self,
#   ) -> Dict[str, Tuple[float, float]]:
#     precios: Dict[str, Tuple[float, float]] = {}
#     if not os.path.exists(RUTA_COMPETENCIA):
#       return precios
#     with open(
#       RUTA_COMPETENCIA, "r", newline="", encoding="utf-8"
#     ) as f:
#       for fila in csv.DictReader(f):
#         precios[fila["isbn"]] = (
#           float(fila.get("precio_ars", 0.0) or 0.0),
#           float(fila.get("precio_usd", 0.0) or 0.0),
#         )
#     return precios
#
#   def comparar(
#     self, isbn: str, precio_propio_ars: float,
#     precio_propio_usd: float,
#   ) -> str:
#     """Compara los precios propios (ARS y USD) contra Cúspide."""
#     precios: Dict[str, Tuple[float, float]] = (
#       self._cargar_precios_competencia()
#     )
#     if isbn not in precios:
#       return "Sin datos de competencia."
#     precio_comp_ars, precio_comp_usd = precios[isbn]
#     resultado_ars: str = self._comparar_monto(
#       precio_propio_ars, precio_comp_ars, "ARS"
#     )
#     resultado_usd: str = self._comparar_monto(
#       precio_propio_usd, precio_comp_usd, "USD"
#     )
#     return f"{resultado_ars} | {resultado_usd}"
#
#   def _comparar_monto(
#     self, propio: float, competencia: float, moneda: str
#   ) -> str:
#     """Compara un monto propio contra el de la competencia."""
#     if propio < competencia:
#       return f"{moneda}: más barato (Cúspide ${competencia})"
#     if propio > competencia:
#       return f"{moneda}: más caro (Cúspide ${competencia})"
#     return f"{moneda}: igual precio"


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
    """Retorna un resumen de cada libro con precios (ARS/USD)."""
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
