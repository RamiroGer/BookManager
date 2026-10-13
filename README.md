# Book Manager

## Sprint 2

### Objetivo

Persistir el sistema en una base de datos relacional con el ORM
SQLAlchemy, migrar los datos cargados en archivos CSV a tablas
relacionales y consultar una API externa para obtener la cotización
del dólar. Se consolidan las bases de manejo de bases de datos,
normalización, conexión segura y carga inicial.

### Introducción y contexto

Una librería con venta al público gestiona su inventario de libros
tomando como referencia el sitio [Cúspide](https://www.cuspide.com/).
En el Sprint 1 el sistema guardaba todo en archivos CSV. En este
sprint, partiendo del último push del Sprint 1 (rama `Sprint_1`), se
trabaja sobre la rama `Sprint_2` para que toda la aplicación use una
base de datos PostgreSQL en Supabase.

### Qué cambió respecto del Sprint 1

- `database/connection.py`: clase `ConexionDB` y context manager
  `transaccion()` (commit al finalizar, rollback ante error).
- `models/models.py`: ocho tablas con claves foráneas, restricciones
  `unique` y borrado en cascada de precios y stock de un libro.
- `migrations/migrations.py`: `migrar_datos` lee los CSV, genera un
  archivo `.sql` por tabla en `migrations/sql` y los ejecuta.
- `repositories/repositories.py`: mismos repositorios del Sprint 1
  pero sobre la base, por lo que servicios y consola casi no cambian.
- `services/services.py`: `ServicioCotizacionDolar.obtener_cotizaciones`
  descarga las cotizaciones de DolarAPI y las registra.
- `ui/console.py`: tres opciones nuevas (obtener cotizaciones por
  API, lista de precios bimonetaria y exportación de precios a CSV).

### Decisiones de diseño

**Supabase (PostgreSQL).** La base es un servicio en la nube del
proyecto del grupo. La URL y la contraseña se cargan en una celda de
credenciales, nunca en el código, y `ConexionDB` las toma del entorno.

**Entidades y modelos separados.** Las entidades POO del Sprint 1
no cambian. Los repositorios traducen entre el modelo de SQLAlchemy y
la entidad de dominio.

**Migración idempotente.** Los `.sql` usan `INSERT ... ON CONFLICT DO
NOTHING`, de modo que ejecutar la migración varias veces no duplica
datos. Después de migrar se ajustan las secuencias de los ids. Las filas que referencian un registro inexistente (por ejemplo, un precio de un libro borrado en el Sprint 1) se omiten con un aviso, para no violar las claves foráneas.
`main()` migra los CSV automáticamente cuando la base está vacía.

**API del dólar.** La URL se lee del archivo `.env` (`API_URL`) con
`python-dotenv`. Los nombres de la API se normalizan a los del
sistema (Bolsa a MEP, Contado con liquidación a CCL). Si falla la
conexión se informa el error y se puede cargar la cotización a mano,
para que el sistema nunca dependa de un servicio externo.

**Comparación con la competencia.** Sigue deshabilitada: requiere web
scraping (Tema 9), que todavía no se vio en la cursada.

### Estructura del proyecto

```
book_manager/
├── src/
│   └── book_manager/
│       ├── database/       # ConexionDB y transacciones
│       ├── entities/       # Modelo de dominio (POO)
│       ├── models/         # Tablas de SQLAlchemy
│       ├── preload_data/   # Datos de origen para la migración
│       ├── repositories/   # Persistencia en base de datos
│       ├── services/       # Lógica de negocio y API del dólar
│       ├── migrations/     # migrar_datos, csv/ y sql/
│       ├── ui/             # Interfaz de consola (CLI)
│       └── main.py         # Punto de entrada
├── .env
├── CHANGELOG.md
├── README.md
└── requirements.txt
```

### Ejecución

```python
from book_manager.main import main
main(import_default_data=False)
```

### Sprint 1

Persistencia en archivos CSV con el patrón Repository, entidades con
encapsulamiento mediante properties, servicios de negocio y una
interfaz de consola con CRUD completo. La comparación con la
competencia quedó deshabilitada por requerir web scraping.
