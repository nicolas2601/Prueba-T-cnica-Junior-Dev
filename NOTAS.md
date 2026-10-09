# Notas de la solución

## Qué cambié
- `app.py`: `POST /api/orders/<id>/ship` solo envía pedidos `pendiente`. La condición está dentro del
  `UPDATE ... WHERE status = 'pendiente'` y se revisa `rowcount`, así que la regla es atómica (no hay
  ventana entre leer y escribir). Cancelado devuelve 409 y conserva su estado; enviado, 409; inexistente, 404.
- `templates/index.html` y `static/style.css`: un banner `role="alert"` muestra el mensaje del servidor.
  Si la respuesta no es JSON (por ejemplo un 404 de Flask) o no hay red, muestra un mensaje genérico.
  Una recarga fallida ya no borra la tabla, y el botón solo se habilita para pedidos pendientes.

## Cómo lo verifiqué
- Antes del cambio: `POST /api/orders/3/ship` (pedido cancelado) devolvía 200 y quedaba `enviado`.
- Después, contra la API: pendiente a enviado (200 y persiste), cancelado (409, sigue cancelado),
  ya enviado (409), inexistente (404) y dos envíos simultáneos sobre el mismo pedido (uno 200, otro 409).
- En el navegador: rechazo 409 con pedido cancelado por detrás de la interfaz, respuesta no JSON, red caída,
  recarga fallida tras un envío correcto y fallo de la primera carga.
- No probado: lectores de pantalla reales (NVDA, VoiceOver) con el banner.

## Problemas conocidos (no los corregí para mantener la solución pequeña)
1. `with connect() as con` confirma o revierte la transacción pero no cierra la conexión.
   Propuesta: `contextlib.closing(connect())` o una conexión por request con `teardown_appcontext`.
2. `sqlite3.connect` crea una base vacía si `data/orders.sqlite3` no existe, y el error llega como un 500
   genérico. Propuesta: abrir con `mode=rw` y avisar de que falta ejecutar `python seed.py`.
3. `app.run(debug=True)` es solo para desarrollo local; en producción usar un servidor WSGI.
4. `SHIP_REJECTIONS[row["status"]]` asume el `CHECK` de `seed.py`. Con un esquema sin ese `CHECK` un estado
   desconocido daría un 500. Propuesta: `.get(...)` con un mensaje genérico.
5. `seed.py` usa `INSERT OR IGNORE`: no restaura datos ya modificados. Para reiniciar, borrar
   `data/orders.sqlite3` y volver a ejecutarlo.
