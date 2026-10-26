"""Servicios de lógica de negocio para Book Manager."""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import urllib.request
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from book_manager.database.connection import ConexionDB

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
RUTA_SRC: str = os.path.join(RUTA_BASE, "src")
RUTA_REPORTES: str = os.path.join(
  os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
  "reportes",
)
URL_CUSPIDE: str = "https://cuspide.com"
COLUMNAS_COMPARACION: List[str] = [
  "libro", "precio_interno", "precio_web", "diferencia",
  "alerta", "url", "fecha_extraccion",
]

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
      texto_fecha: str = str(item.get("fechaActualizacion") or "")[:10]
      fecha: date = (
        date.fromisoformat(texto_fecha) if texto_fecha else date.today()
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
    fecha: Optional[date] = None,
  ) -> CotizacionDolar:
    """Registra la cotización de un tipo y fecha, o la actualiza."""
    tipo: Optional[TipoCotizacion] = self._repo_tipo.leer_por_id(
      tipo_id
    )
    if tipo is None:
      raise ValueError(f"No existe el tipo id={tipo_id}.")
    fecha_real: date = fecha or date.today()
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

  def mapa_precios(self) -> Dict[Tuple[int, str], Precio]:
    """Carga todos los precios una sola vez, por (libro_id, moneda)."""
    return {
      (p.libro.id, p.moneda.codigo): p
      for p in self._repo_precio.leer_todos()
    }

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
    self,
    libro_id: int,
    monto_ars: float,
    cotizacion: Optional[CotizacionDolar] = None,
  ) -> Precio:
    """Actualiza el precio en ARS y guarda la cotización usada."""
    precio_ars: Optional[Precio] = self.precio_por_moneda(
      libro_id, "ARS"
    )
    if precio_ars is None:
      raise ValueError("El libro no tiene precio en ARS.")
    precio_ars.monto = monto_ars
    precio_ars.cotizacion = cotizacion
    return self._repo_precio.actualizar(precio_ars)

  def lista_bimonetaria(
    self, codigo_otra: str
  ) -> List[Tuple[Libro, Optional[float], Optional[float]]]:
    """Lista cada libro con su precio en ARS y en otra moneda."""
    precios: Dict[Tuple[int, str], Precio] = self.mapa_precios()
    lista: List[Tuple[Libro, Optional[float], Optional[float]]] = []
    for libro in self._repo_libro.leer_todos():
      precio_ars: Optional[Precio] = precios.get((libro.id, "ARS"))
      precio_otra: Optional[Precio] = precios.get(
        (libro.id, codigo_otra.upper())
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
    precios: Dict[Tuple[int, str], Precio] = self.mapa_precios()
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
          precio: Optional[Precio] = precios.get(
            (libro.id, moneda.codigo)
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
    cotizacion: Optional[CotizacionDolar] = None,
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
      Precio(
        libro=libro,
        moneda=moneda_ars,
        monto=precio_ars,
        cotizacion=cotizacion,
      )
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
    precios: Dict[int, List[Precio]] = {}
    for precio in self._servicio_precio.mapa_precios().values():
      precios.setdefault(precio.libro.id, []).append(precio)
    stock: Dict[int, Stock] = {
      s.libro.id: s for s in self._repo_stock.leer_todos()
    }
    resumen: List[Dict[str, object]] = []
    for libro in self._repo_libro.leer_todos():
      existencia: Optional[Stock] = stock.get(libro.id)
      resumen.append({
        "libro": libro,
        "precios": precios.get(libro.id, []),
        "cantidad": existencia.cantidad if existencia else 0,
      })
    return resumen


def _escribir_csv(ruta: str, filas: List[Dict[str, object]]) -> None:
  """Escribe las comparaciones en CSV, con encabezado aunque esté vacío."""
  with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
    escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS_COMPARACION)
    escritor.writeheader()
    escritor.writerows(filas)



class ServicioScraping:
  """Compara los precios internos con los publicados en Cúspide."""

  def __init__(
    self,
    conexion: ConexionDB,
    repo_libro: RepositorioLibro,
    servicio_precio: ServicioPrecio,
    base_url: str = URL_CUSPIDE,
  ) -> None:
    self._conexion = conexion
    self._repo_libro = repo_libro
    self._servicio_precio = servicio_precio
    self._base_url = base_url

  def ejecutar(self, umbral: float) -> Dict[str, object]:
    """Ejecuta el scraper y genera el CSV de comparación y el de alertas.

    Args:
      umbral: Diferencia en pesos desde la cual se genera una alerta.

    Returns:
      Rutas de los CSV generados y cantidades de comparaciones y alertas.
    """
    if umbral < 0:
      raise ValueError("El umbral no puede ser negativo.")
    os.makedirs(RUTA_REPORTES, exist_ok=True)
    ruta_titulos: str = os.path.join(RUTA_REPORTES, "titulos_busqueda.json")
    ruta_resultados: str = os.path.join(
      RUTA_REPORTES, "resultados_scraping.jsonl"
    )
    titulos: List[str] = [
      libro.titulo for libro in self._repo_libro.leer_todos()
    ]
    with open(ruta_titulos, "w", encoding="utf-8") as archivo:
      json.dump(titulos, archivo, ensure_ascii=False)

    self._correr_spider(ruta_titulos, ruta_resultados)
    comparaciones: List[Dict[str, object]] = self._comparar(
      self._leer_resultados(ruta_resultados), umbral
    )
    alertas: List[Dict[str, object]] = [
      fila for fila in comparaciones if fila["alerta"] == "Sí"
    ]
    marca: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta_comparacion: str = os.path.join(
      RUTA_REPORTES, f"comparacion_{marca}.csv"
    )
    ruta_alertas: str = os.path.join(RUTA_REPORTES, f"alertas_{marca}.csv")
    _escribir_csv(ruta_comparacion, comparaciones)
    _escribir_csv(ruta_alertas, alertas)
    return {
      "comparadas": len(comparaciones),
      "alertas": len(alertas),
      "ruta_comparacion": ruta_comparacion,
      "ruta_alertas": ruta_alertas,
    }

  def _correr_spider(self, ruta_titulos: str, ruta_resultados: str) -> None:
    """Ejecuta el spider en un proceso aparte y espera a que termine."""
    env: Dict[str, str] = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
      parte for parte in [RUTA_SRC, os.environ.get("PYTHONPATH", "")]
      if parte
    )
    proceso = subprocess.run(
      [
        sys.executable, "-m", "book_manager.scraper.ejecutor",
        "--titulos", ruta_titulos,
        "--salida", ruta_resultados,
        "--base-url", self._base_url,
      ],
      env=env,
      capture_output=True,
      text=True,
      check=False,
    )
    if proceso.returncode != 0:
      raise ConnectionError(
        f"Falló el scraping: {proceso.stderr[-300:]}"
      )

  def _leer_resultados(self, ruta: str) -> List[Dict[str, object]]:
    """Lee los items que dejó el scraper en formato JSON Lines."""
    if not os.path.exists(ruta):
      return []
    with open(ruta, "r", encoding="utf-8") as archivo:
      return [json.loads(linea) for linea in archivo if linea.strip()]

  def _comparar(
    self, resultados: List[Dict[str, object]], umbral: float
  ) -> List[Dict[str, object]]:
    """Calcula la diferencia entre el precio web y el interno en ARS."""
    precios = self._servicio_precio.mapa_precios()
    precio_interno: Dict[str, float] = {}
    for libro in self._repo_libro.leer_todos():
      precio_ars = precios.get((libro.id, "ARS"))
      if precio_ars is not None:
        precio_interno[libro.titulo] = precio_ars.monto
    comparaciones: List[Dict[str, object]] = []
    for resultado in resultados:
      titulo: str = str(resultado["titulo_buscado"])
      if titulo not in precio_interno:
        continue
      interno: float = precio_interno[titulo]
      web: float = float(resultado["precio_web"])
      diferencia: float = round(web - interno, 2)
      comparaciones.append({
        "libro": titulo,
        "precio_interno": interno,
        "precio_web": web,
        "diferencia": diferencia,
        "alerta": "Sí" if abs(diferencia) >= umbral else "No",
        "url": resultado["url"],
        "fecha_extraccion": resultado["fecha_extraccion"],
      })
    return comparaciones
