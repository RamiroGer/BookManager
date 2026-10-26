"""Pipelines que validan y exportan los items del scraper."""
import json
from typing import Any, Optional, TextIO

from scrapy.exceptions import DropItem


class ValidarPrecioPipeline:
  """Descarta las publicaciones que no tienen un precio válido."""

  def process_item(self, item: Any) -> Any:
    """Rechaza los items sin precio web."""
    if not item.get("precio_web"):
      raise DropItem(f"Sin precio válido: {item.get('url')}")
    return item


class ExportarJsonLinesPipeline:
  """Escribe cada item como una línea de un archivo JSON Lines."""

  def __init__(self, ruta_salida: str) -> None:
    self._ruta_salida: str = ruta_salida
    self._archivo: Optional[TextIO] = None

  @classmethod
  def from_crawler(cls, crawler: Any) -> "ExportarJsonLinesPipeline":
    """Toma la ruta de salida de la configuración del proceso."""
    return cls(crawler.settings.get("RUTA_SALIDA"))

  def open_spider(self) -> None:
    """Abre el archivo de salida."""
    self._archivo = open(self._ruta_salida, "w", encoding="utf-8")

  def close_spider(self) -> None:
    """Cierra el archivo de salida."""
    if self._archivo is not None:
      self._archivo.close()

  def process_item(self, item: Any) -> Any:
    """Escribe el item como una línea JSON."""
    linea: str = json.dumps(dict(item), ensure_ascii=False)
    self._archivo.write(linea + "\n")
    return item
