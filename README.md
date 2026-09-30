# Book Manager

## Sprint 1

### Objetivo

Aplicar los conocimientos de programación orientada a objetos y
persistencia de datos en archivos para modernizar el sistema de
inventario de una librería, tomando como referencia el sitio
[Cúspide](https://www.cuspide.com/).

### Contexto

Una librería con venta al público necesita gestionar su
inventario de libros, cotizar precios en distintas monedas
siguiendo la cotización del dólar, y comparar esos precios
contra la competencia web.

El sistema se implementa como una aplicación de consola (CLI) en
Python puro (solo librería estándar, sin instalar paquetes),
aplicando:

- Programación orientada a objetos con encapsulación mediante
  properties.
- Persistencia en archivos CSV a través del patrón Repository,
  con una interfaz genérica `IRepositorio`.
- Servicios de lógica de negocio separados de la persistencia y
  de la interfaz de usuario.
- Cada libro se carga con precio en ARS y en USD, tal como
  los muestra Cúspide.
- Cotización del dólar cargada manualmente, sin API (ver
  sección siguiente).

### Decisión de diseño: cotización del dólar (sin API)

El enunciado menciona seguir de cerca la cotización del dólar. La
consigna del trabajo indica resolverlo **sin API**, por lo que el
sistema no consulta ningún servicio externo: las cotizaciones se
cargan manualmente desde la opción "Cotizaciones del Dólar" del
menú (o al precargar datos, con un valor de referencia por tipo) y
se guardan con su fecha, formando un histórico por tipo.

Con la última cotización registrada se calcula el precio ARS
sugerido de cada libro (precio USD x cotización de venta) y se lo
compara contra el precio ARS vigente.

La versión que consultaba [DolarAPI](https://dolarapi.com/) con
`urllib.request` no se eliminó: quedó **comentada** en
`services.py` (`obtener_cotizacion_automatica`) y en `console.py`,
para poder habilitarla en un sprint futuro.

### Decisión de diseño: comparación con la competencia
(funcionalidad deshabilitada)

El enunciado menciona "comparar precios automáticamente con la
competencia web", lo cual en la práctica requiere técnicas de
web scraping. Ese tema (Tema 9) todavía no fue visto en la
cursada, y usar herramientas no vistas está fuera de lo permitido
por la consigna.

Por ese motivo, se diseñó e implementó la funcionalidad completa
(`ServicioComparacionCompetencia`, el archivo de referencia
`migrations/csv/competencia.csv` con precios simulados en ARS y
USD, y el reporte correspondiente en la consola), pero se dejó
**comentada** en el código en vez de eliminarla, para poder
habilitarla fácilmente en un sprint futuro una vez visto el tema.
Por este motivo la opción de menú "Comparación con Competencia"
no está disponible en esta entrega.

### Decisión de diseño: aplicar el precio sugerido

Varios libros no contaban con un precio calculado para ciertos
tipos de cotización (Oficial, Blue, etc.), ya que originalmente
solo se cargaban con un precio ARS y USD de referencia (Cúspide).
Para resolverlo, la opción de Precios permite elegir un libro y un
tipo de cotización: si no hay una cotización registrada para ese
tipo, el sistema la pide en el momento por consola. Con la cotización
obtenida, calcula el precio ARS sugerido y ofrece aplicarlo
directamente al libro, actualizando el precio vigente.

### Estructura del proyecto

```
book_manager/
├── src/
│   └── book_manager/
│       ├── entities/       # Modelo de dominio (POO)
│       ├── repositories/   # Persistencia CSV (patrón Repository)
│       ├── services/       # Lógica de negocio
│       ├── preload_data/   # Datos de ejemplo
│       ├── migrations/csv/ # Archivos CSV de persistencia
│       ├── ui/             # Interfaz de consola (CLI)
│       └── main.py         # Punto de entrada
├── CHANGELOG.md
├── README.md
└── requirements.txt
```
