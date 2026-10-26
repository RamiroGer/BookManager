"""Migración de datos desde archivos CSV hacia la base de datos."""
from __future__ import annotations

import csv
import os
from datetime import date
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy import text

from book_manager.database.connection import ConexionDB
import book_manager.models.models  # noqa: F401

RUTA_CSV: str = os.path.join(
  os.path.dirname(os.path.abspath(__file__)), "csv"
)
RUTA_SQL: str = os.path.join(
  os.path.dirname(os.path.abspath(__file__)), "sql"
)

# Orden de migración respetando las claves foráneas:
# archivo CSV -> (tabla, columnas con su tipo).
TABLAS: List[Tuple[str, str, Dict[str, str]]] = [
  ("generos.csv", "generos", {"id": "int", "nombre": "str"}),
  (
    "editoriales.csv", "editoriales",
    {"id": "int", "nombre": "str", "pais": "str"},
  ),
  (
    "monedas.csv", "monedas",
    {"id": "int", "codigo": "str", "nombre": "str"},
  ),
  (
    "tipos_cotizacion.csv", "tipos_cotizacion",
    {"id": "int", "nombre": "str"},
  ),
  (
    "libros.csv", "libros",
    {
      "id": "int", "isbn": "str", "titulo": "str", "autor": "str",
      "editorial_id": "int", "genero_id": "int",
    },
  ),
  (
    "precios.csv", "precios",
    {
      "id": "int", "libro_id": "int", "moneda_id": "int",
      "monto": "float",
    },
  ),
  (
    "stocks.csv", "stocks",
    {"id": "int", "libro_id": "int", "cantidad": "int"},
  ),
  (
    "cotizaciones.csv", "cotizaciones",
    {
      "id": "int", "tipo_id": "int", "fecha": "date",
      "valor_compra": "float", "valor_venta": "float",
    },
  ),
]


def _literal_sql(valor: str, tipo: str) -> str:
  """Convierte un valor del CSV en un literal SQL."""
  if tipo == "int":
    return str(int(valor))
  if tipo == "float":
    return str(float(valor))
  if tipo == "date":
    return "'" + date.fromisoformat(valor).isoformat() + "'"
  return "'" + valor.replace("'", "''") + "'"


PADRES_FK: Dict[str, str] = {
  "editorial_id": "editoriales",
  "genero_id": "generos",
  "libro_id": "libros",
  "moneda_id": "monedas",
  "tipo_id": "tipos_cotizacion",
}


def _ids_en_base(conexion: ConexionDB, tabla: str) -> Set[str]:
  """Devuelve los ids que realmente existen en una tabla de la base."""
  with conexion.transaccion() as sesion:
    filas = sesion.execute(text(f"SELECT id FROM {tabla};")).scalars()
    return {str(id_) for id_ in filas}


def _generar_inserts(
  ruta_csv: str,
  tabla: str,
  columnas: Dict[str, str],
  ids_padres: Dict[str, Set[str]],
) -> Tuple[List[str], int]:
  """Genera un INSERT por fila válida y cuenta las filas huérfanas.

  Una fila es huérfana si referencia un id que no existe en la tabla
  padre; se omite para no romper la clave foránea.

  Returns:
    Sentencias generadas y cantidad de filas omitidas.
  """
  sentencias: List[str] = []
  huerfanas: int = 0
  with open(ruta_csv, "r", newline="", encoding="utf-8") as f:
    for fila in csv.DictReader(f):
      referencias_rotas: bool = any(
        fila[col] not in ids_padres.get(PADRES_FK[col], set())
        for col in columnas
        if col in PADRES_FK
      )
      if referencias_rotas:
        huerfanas += 1
        continue
      valores: str = ", ".join(
        _literal_sql(fila[col], tipo)
        for col, tipo in columnas.items()
      )
      sentencias.append(
        f"INSERT INTO {tabla} "
        f"({', '.join(columnas)}) VALUES ({valores}) "
        "ON CONFLICT DO NOTHING;"
      )
  return sentencias, huerfanas


def _ejecutar_sql(
  conexion: ConexionDB, ruta_sql: str
) -> int:
  """Ejecuta las sentencias de un archivo .sql y cuenta filas."""
  with open(ruta_sql, "r", encoding="utf-8") as f:
    sentencias: List[str] = [
      linea.strip() for linea in f if linea.strip()
    ]
  with conexion.transaccion() as sesion:
    for sentencia in sentencias:
      sesion.execute(text(sentencia))
  return len(sentencias)


def _reiniciar_secuencias(conexion: ConexionDB) -> None:
  """Ajusta las secuencias de id tras insertar ids explícitos."""
  with conexion.transaccion() as sesion:
    for _, tabla, _ in TABLAS:
      sesion.execute(text(
        f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
        f"COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {tabla};"
      ))


def migrar_datos(
  carpeta_csvs: str,
  carpeta_sqls: str,
  conexion: Optional[ConexionDB] = None,
) -> Dict[str, int]:
  """Migra los CSV a la base generando un archivo .sql por tabla.

  Args:
    carpeta_csvs: Carpeta donde están los archivos CSV de origen.
    carpeta_sqls: Carpeta donde se guardan los archivos SQL.
    conexion: Conexión a la base; si no se indica crea una nueva.

  Returns:
    Cantidad de sentencias ejecutadas por tabla.
  """
  conexion = conexion or ConexionDB()
  conexion.crear_tablas()
  os.makedirs(carpeta_sqls, exist_ok=True)

  resumen: Dict[str, int] = {}
  for orden, (archivo, tabla, columnas) in enumerate(TABLAS, 1):
    ruta_csv: str = os.path.join(carpeta_csvs, archivo)
    if not os.path.exists(ruta_csv):
      continue
    ids_padres: Dict[str, Set[str]] = {
      padre: _ids_en_base(conexion, padre)
      for padre in PADRES_FK.values()
    }
    sentencias, huerfanas = _generar_inserts(
      ruta_csv, tabla, columnas, ids_padres
    )
    if huerfanas:
      print(
        f"Aviso: {tabla}: {huerfanas} filas omitidas por "
        "referenciar registros inexistentes en la base."
      )
    ruta_sql: str = os.path.join(
      carpeta_sqls, f"{orden:02d}_{tabla}.sql"
    )
    with open(ruta_sql, "w", encoding="utf-8") as f:
      f.write("\n".join(sentencias) + "\n")
    resumen[tabla] = _ejecutar_sql(conexion, ruta_sql)
  _reiniciar_secuencias(conexion)
  return resumen


def cargar_datos_sql(
  conexion: ConexionDB, carpeta_sqls: str
) -> Dict[str, int]:
  """Ejecuta en la base los archivos .sql de una carpeta, en orden.

  Args:
    conexion: Conexión a la base donde se cargan los datos.
    carpeta_sqls: Carpeta con los archivos .sql generados en la migración.

  Returns:
    Cantidad de sentencias ejecutadas por archivo.
  """
  resumen: Dict[str, int] = {}
  for archivo in sorted(os.listdir(carpeta_sqls)):
    if archivo.endswith(".sql"):
      ruta_sql: str = os.path.join(carpeta_sqls, archivo)
      resumen[archivo] = _ejecutar_sql(conexion, ruta_sql)
  _reiniciar_secuencias(conexion)
  return resumen
