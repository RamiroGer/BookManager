"""Loaders que limpian los datos extraídos antes de crear el item."""
from typing import Optional

from itemloaders.processors import Join, MapCompose, TakeFirst
from scrapy.loader import ItemLoader


def limpiar_texto(texto: str) -> str:
  """Quita espacios repetidos y saltos de línea de un texto."""
  return " ".join(texto.split())


def precio_a_numero(texto: str) -> Optional[float]:
  """Convierte '$ 189.900,00' en 189900.0; None si no es un precio."""
  limpio: str = texto.replace("$", "").replace(".", "")
  limpio = limpio.replace(",", ".").strip()
  try:
    return float(limpio)
  except ValueError:
    return None


class LibroWebLoader(ItemLoader):
  """Carga un LibroWebItem aplicando la limpieza de cada campo."""

  default_output_processor = TakeFirst()

  titulo_web_in = MapCompose(limpiar_texto)
  precio_web_in = MapCompose(precio_a_numero)
  formas_pago_in = MapCompose(limpiar_texto)
  formas_pago_out = Join(" | ")
  descripcion_in = MapCompose(limpiar_texto)
  descripcion_out = Join(" ")
