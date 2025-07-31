
# Juego del Ahogado en Python

¡Bienvenido al Juego del Ahorcado! Este es un juego interactivo desarrollado en Python usando Tkinter, con una interfaz gráfica, soporte para MySQL, sonidos, y un diseño visual con colores personalizados. El objetivo es adivinar una palabra oculta letra por letra antes de que se complete el dibujo del ahorcado.


![Captura del Juego](https://github.com/pedro72635/ahorcado_python/raw/main/screenshot.png)
## Caracteristicas

Interfaz gráfica: Desarrollada con Tkinter, con botones en colores personalizados (verde, rojo, azul claro, azul medio, gris azulado) y texto blanco legible.

Base de datos: Utiliza MySQL para gestionar puntuaciones y palabras_shelf.db para almacenamiento de palabras.

Efectos visuales y sonoros: Incluye un degradado de fondo, dibujo dinámico del ahorcado, sonidos para acciones, y un destello verde al acertar.

Menú intuitivo: Navegación sin duplicaciones al volver al menú principal.



## Requisitos:

Python: Versión 3.8 o superior.

MySQL: Servidor MySQL configurado (e.g., MySQL Community Server).

Dependencias: Instala las librerías requeridas desde requirements.txt

## Instalación

Instalación

Clona el repositorio:
```
git clone https://github.com/pedro72635/ahorcado_python.git
cd ahorcado_python
```

Crea un entorno virtual (opcional, recomendado):
```
python -m venv .venv
.venv\Scripts\activate
```

Instala las dependencias:
```
pip install -r requirements.txt
```

Configura MySQL:
Asegúrate de tener MySQL instalado y en ejecución.

Crea una base de datos llamada ahorcado:
```
CREATE DATABASE ahorcado;
```


Actualiza las credenciales en ahorcado.py (variable MYSQL_CONFIG) con tus credenciales:
```
MYSQL_CONFIG = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'ahorcado'
}
```
## Ejecución
Ejecuta el juego:
Desde la consola de comandos ejecuta el comando:
```
python ahorcado.py
```
