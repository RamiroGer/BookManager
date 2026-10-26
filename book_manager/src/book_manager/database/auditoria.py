"""Decorador que registra en la tabla de auditoría cada operación."""
from __future__ import annotations

import functools
from datetime import datetime
from typing import Any, Callable, TypeVar, cast

from book_manager.database.connection import ConexionDB
from book_manager.models.models import AuditoriaModel

F = TypeVar("F", bound=Callable[..., Any])

LONGITUD_ACCION: int = 100
LONGITUD_DETALLES: int = 500


def registrar_auditoria(
  conexion: ConexionDB, accion: str, detalles: str
) -> None:
  """Inserta un registro de auditoría en su propia transacción."""
  with conexion.transaccion() as sesion:
    sesion.add(
      AuditoriaModel(
        accion=accion[:LONGITUD_ACCION],
        fecha=datetime.now(),
        detalles=detalles[:LONGITUD_DETALLES],
      )
    )


def auditar(accion: str) -> Callable[[F], F]:
  """Registra la operación con su resultado, o con su error si falla.

  El objeto decorado debe tener el atributo ``_conexion``.
  """
  def decorador(funcion: F) -> F:
    @functools.wraps(funcion)
    def envoltorio(self: Any, *args: Any, **kwargs: Any) -> Any:
      try:
        resultado: Any = funcion(self, *args, **kwargs)
      except Exception as error:
        registrar_auditoria(
          self._conexion,
          f"ERROR: {accion}",
          f"{type(self).__name__}: {error}",
        )
        raise
      registrar_auditoria(
        self._conexion,
        accion,
        f"{type(self).__name__}: {resultado!r}",
      )
      return resultado
    return cast(F, envoltorio)
  return decorador
