"""Spider que busca los libros del catálogo en el sitio de Cúspide."""
import json
from datetime import datetime
from typing import AsyncIterator, Iterator, List, Optional, Set
from urllib.parse import quote_plus, urlparse

import scrapy
from scrapy.http import Request, Response

from book_manager.scraper.items import LibroWebItem
from book_manager.scraper.loaders import LibroWebLoader

URL_BASE: str = "https://cuspide.com"
MAX_RESULTADOS: int = 10

# Los selectores se escriben para un sitio WooCommerce. Si el sitio
# cambia su marcado, alcanza con ajustar estas listas.
SELECTORES_TITULO: List[str] = [
  "h1.product_title::text",
  "meta[property='og:title']::attr(content)",
]
SELECTORES_PRECIO: List[str] = [
  "p.price ins bdi::text",
  "p.price bdi::text",
  "span.woocommerce-Price-amount bdi::text",
]
SELECTORES_IMAGEN: List[str] = [
  "meta[property='og:image']::attr(content)",
  "img.wp-post-image::attr(src)",
]
SELECTORES_DESCRIPCION: List[str] = [
  "div.woocommerce-Tabs-panel--description ::text",
  "div.woocommerce-product-details__short-description ::text",
]
PALABRAS_PAGO: List[str] = [
  "tarjeta",
  "transferencia",
  "mercadopago",
  "mobbex",
  "rapipago",
  "pago fácil",
  "depósito",
]


def normalizar(texto: str) -> str:
  """Pasa un texto a minúsculas y quita los espacios repetidos."""
  return " ".join(texto.lower().split())


SEPARADORES_TITULO: List[str] = [" - ", " – ", ": ", " (", ", "]


def coincide_titulo(titulo: str, titulo_web: str) -> bool:
  """Acepta el título exacto o seguido de un subtítulo o edición."""
  buscado: str = normalizar(titulo)
  web: str = normalizar(titulo_web)
  if web == buscado:
    return True
  return any(
    web.startswith(buscado + separador) for separador in SEPARADORES_TITULO
  )


def primer_valor(respuesta: Response, selectores: List[str]) -> Optional[str]:
  """Devuelve el primer texto no vacío que encuentre algún selector."""
  for selector in selectores:
    for valor in respuesta.css(selector).getall():
      if valor.strip():
        return valor.strip()
  return None


def textos_de(respuesta: Response, selectores: List[str]) -> List[str]:
  """Devuelve los trozos de texto del primer selector que encuentre datos."""
  for selector in selectores:
    textos: List[str] = [
      texto for texto in respuesta.css(selector).getall()
      if texto.strip()
    ]
    if textos:
      return textos
  return []


class CuspideSpider(scrapy.Spider):
  """Busca cada libro del catálogo y extrae sus publicaciones."""

  name: str = "cuspide"

  def __init__(
    self,
    titulos_archivo: str,
    base_url: str = URL_BASE,
    **kwargs,
  ) -> None:
    super().__init__(**kwargs)
    self.base_url: str = base_url.rstrip("/")
    self.allowed_domains: List[str] = [urlparse(self.base_url).hostname]
    with open(titulos_archivo, "r", encoding="utf-8") as archivo:
      self.titulos: List[str] = json.load(archivo)

  async def start(self) -> AsyncIterator[Request]:
    """Punto de inicio de Scrapy 2.13 en adelante."""
    for solicitud in self._solicitudes_busqueda():
      yield solicitud

  def start_requests(self) -> Iterator[Request]:
    """Punto de inicio para versiones de Scrapy anteriores a 2.13."""
    return self._solicitudes_busqueda()

  def _solicitudes_busqueda(self) -> Iterator[Request]:
    """Genera una búsqueda por cada título del catálogo."""
    for titulo in self.titulos:
      url: str = (
        f"{self.base_url}/?s={quote_plus(titulo)}&post_type=product"
      )
      yield Request(
        url,
        callback=self.parse_busqueda,
        cb_kwargs={"titulo": titulo},
      )

  def parse_busqueda(
    self, response: Response, titulo: str
  ) -> Iterator[Request]:
    """Mira los primeros resultados y sigue los que son el libro buscado."""
    vistos: Set[str] = set()
    for enlace in response.css("a[href*='/producto/']"):
      texto: str = " ".join(enlace.css("::text").getall()).strip()
      href: Optional[str] = enlace.attrib.get("href")
      if not texto or not href or href in vistos:
        continue
      if len(vistos) >= MAX_RESULTADOS:
        break
      vistos.add(href)
      if coincide_titulo(titulo, texto):
        yield response.follow(
          href,
          callback=self.parse_producto,
          cb_kwargs={"titulo": titulo, "titulo_web": texto},
        )

  def parse_producto(
    self, response: Response, titulo: str, titulo_web: str
  ) -> Iterator[LibroWebItem]:
    """Extrae precio, imagen, formas de pago y descripción."""
    cargador = LibroWebLoader(item=LibroWebItem(), response=response)
    cargador.add_value("titulo_buscado", titulo)
    cargador.add_value(
      "titulo_web", primer_valor(response, SELECTORES_TITULO) or titulo_web
    )
    cargador.add_value("url", response.url)
    cargador.add_value("url_imagen", primer_valor(response, SELECTORES_IMAGEN))
    cargador.add_value("precio_web", primer_valor(response, SELECTORES_PRECIO))
    cargador.add_value("formas_pago", self._formas_de_pago(response))
    cargador.add_value(
      "descripcion", textos_de(response, SELECTORES_DESCRIPCION)
    )
    cargador.add_value(
      "fecha_extraccion", datetime.now().isoformat(timespec="seconds")
    )
    yield cargador.load_item()

  def _formas_de_pago(self, response: Response) -> List[str]:
    """Busca en el texto de la página las líneas que describen pagos."""
    textos: List[str] = response.xpath(
      "//body//text()[not(ancestor::script) and not(ancestor::style)]"
    ).getall()
    pagos: List[str] = []
    for texto in textos:
      limpio: str = " ".join(texto.split())
      if not limpio or len(limpio) > 200:
        continue
      if any(palabra in limpio.lower() for palabra in PALABRAS_PAGO):
        if limpio not in pagos:
          pagos.append(limpio)
    return pagos
