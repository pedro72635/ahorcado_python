import tkinter as tk
from tkinter import messagebox, ttk
import requests
from collections import Counter
import mysql.connector
from mysql.connector import Error
import random
import pygame
import numpy as np
import asyncio
import platform
import shelve

MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password':'root',
    'database': 'ahorcado'
}

def configurar_base_datos():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS puntuaciones (id INT AUTO_INCREMENT PRIMARY KEY, jugador VARCHAR(50), palabra VARCHAR(50), exito BOOLEAN, idioma VARCHAR(10), fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.commit()
    except Error as e:
        print(f"Error al conectar con MySQL: {e}")
        messagebox.showerror("Error de Base de Datos", f"No se pudo conectar con MySQL: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def guardar_puntuacion(jugador, palabra, exito, idioma):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO puntuaciones (jugador, palabra, exito, idioma) VALUES (%s, %s, %s, %s)", (jugador, palabra, exito, idioma))
        conn.commit()
    except Error as e:
        print(f"Error al guardar puntuación: {e}")
        messagebox.showwarning("Advertencia", "No se pudo guardar la puntuación en la base de datos.")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def generar_sonido(frecuencia, duracion=0.2, volumen=0.05, sample_rate=44100):
    try:
        t = np.linspace(0, duracion, int(sample_rate * duracion), False)
        onda = volumen * np.sin(2 * np.pi * frecuencia * t)
        sonido_array = (onda * 32767).astype(np.int16)
        # Crear array estéreo (2 canales)
        sonido_array = np.column_stack((sonido_array, sonido_array))
        print(f"Shape del sonido_array: {sonido_array.shape}")  # Depuración
        return pygame.mixer.Sound(sonido_array)
    except Exception as e:
        print(f"Error al generar sonido: {e}")
        messagebox.showwarning("Advertencia", f"No se pudo generar el sonido: {e}")
        return None

def obtener_palabra_aleatoria(idioma):
    print(f"Intentando obtener palabra para idioma: {idioma}")
    if idioma == "Español":
        try:
            with shelve.open('palabras_shelf') as db:
                palabras = db.get('palabras', [])
                if not palabras:
                    print("No hay palabras en el archivo shelf, usando palabra de respaldo.")
                    messagebox.showwarning("Advertencia", "No hay palabras en el archivo shelf. Usando palabra de respaldo.")
                    return "casa"
                palabra = random.choice(palabras)
                print(f"Devolviendo palabra en español desde shelf: '{palabra}'")
                return palabra
        except Exception as e:
            print(f"Error al leer el archivo shelf: {e}")
            messagebox.showwarning("Advertencia", f"Error al leer el archivo shelf: {e}. Usando palabra de respaldo.")
            return "casa"
    try:
        response = requests.get("https://random-word-api.herokuapp.com/word?number=10", timeout=5)
        response.raise_for_status()
        palabras = response.json()
        print(f"Palabras obtenidas: {palabras}")
        for palabra_ingles in palabras:
            print(f"Evaluando palabra en inglés: '{palabra_ingles}', longitud: {len(palabra_ingles)}")
            if 4 <= len(palabra_ingles) <= 8:
                print(f"Devolviendo palabra en inglés: '{palabra_ingles}'")
                return palabra_ingles
        print("Ninguna palabra válida encontrada, usando respaldo.")
        return "casa"
    except requests.RequestException as e:
        print(f"Error en Random Word API: {e}")
        messagebox.showwarning("Advertencia", f"Error al obtener palabra en inglés: {e}. Usando palabra de respaldo.")
        return "casa"
    except Exception as e:
        print(f"Error inesperado: {e}")
        messagebox.showwarning("Advertencia", f"Error inesperado: {e}. Usando palabra de respaldo.")
        return "casa"

def mostrar_palabra(palabra, letras_adivinadas):
    return ' '.join(letra if letra in letras_adivinadas else '_' for letra in palabra)

def interpolate_color(color1, color2, factor):
    """Interpolar entre dos colores (hex) según un factor (0 a 1)."""
    r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
    r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"

class JuegoAhorcado:
    def __init__(self, root):
        self.root = root
        self.root.title("Juego del Ahorcado")
        self.root.geometry("800x900")
        self.root.minsize(800, 900)

        # Estilo para Combobox
        style = ttk.Style()
        style.configure("TCombobox", font=("Segoe UI", 12))

        # Fondo con degradado suave
        self.canvas_fondo = tk.Canvas(self.root, width=800, height=900, highlightthickness=0)
        self.canvas_fondo.pack(fill="both", expand=True)
        for y in range(900):
            factor = y / 900
            color = interpolate_color("#bbdefb", "#90caf9", factor)
            self.canvas_fondo.create_line(0, y, 800, y, fill=color)

        # Inicializar mixer con parámetros explícitos
        try:
            pygame.mixer.quit()  # Cerrar cualquier inicialización previa
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            print(f"Configuración del mixer: {pygame.mixer.get_init()}")  # Depuración
        except Exception as e:
            print(f"Error al inicializar el mixer: {e}")
            messagebox.showwarning("Advertencia", f"No se pudo inicializar el mixer de Pygame: {e}")

        # Generar sonidos
        self.sonido_acierto = generar_sonido(440)
        self.sonido_error = generar_sonido(220)
        self.sonido_victoria = generar_sonido(880, duracion=0.5)
        self.sonido_derrota = generar_sonido(110, duracion=0.5)

        # Verificar si los sonidos se crearon correctamente
        if not all([self.sonido_acierto, self.sonido_error, self.sonido_victoria, self.sonido_derrota]):
            messagebox.showwarning("Advertencia", "Uno o más sonidos no se pudieron generar. El juego continuará sin sonidos.")

        # Frames
        self.frame_bienvenida = tk.Frame(self.canvas_fondo, bg="#a8d4fa")
        self.frame_juego = tk.Frame(self.canvas_fondo, bg="#a8d4fa")

        # Widgets del menú (creados una sola vez)
        self.label_titulo = tk.Label(self.frame_bienvenida, text="Juego del Ahorcado", font=("Segoe UI", 28, "bold"), bg="#a8d4fa", fg="#0d47a1")
        self.label_titulo.pack(pady=40)
        self.label_jugador = tk.Label(self.frame_bienvenida, text="Nombre del jugador:", font=("Segoe UI", 16, "bold"), bg="#a8d4fa", fg="#0d47a1")
        self.label_jugador.pack(pady=20)
        self.entry_jugador = tk.Entry(self.frame_bienvenida, font=("Segoe UI", 14), width=20, relief="flat", bg="#e3f2fd", highlightthickness=1, highlightcolor="#0d47a1")
        self.entry_jugador.pack(pady=20)
        self.label_idioma = tk.Label(self.frame_bienvenida, text="Selecciona el idioma:", font=("Segoe UI", 16, "bold"), bg="#a8d4fa", fg="#0d47a1")
        self.label_idioma.pack(pady=20)
        self.idioma = tk.StringVar(value="Español")
        idiomas = ["Español", "Inglés"]
        self.combo_idioma = ttk.Combobox(self.frame_bienvenida, textvariable=self.idioma, values=idiomas, state="readonly", style="TCombobox")
        self.combo_idioma.pack(pady=20)
        self.boton_jugar = tk.Button(self.frame_bienvenida, text="Jugar", font=("Segoe UI", 14), bg="#4CAF50", fg="#FFFFFF", activebackground="#45a049", activeforeground="#FFFFFF", relief="flat", padx=10, pady=5, command=self.iniciar_juego)
        self.boton_jugar.pack(pady=20)
        self.boton_salir = tk.Button(self.frame_bienvenida, text="Salir", font=("Segoe UI", 14), bg="#f44336", fg="#FFFFFF", activebackground="#da190b", activeforeground="#FFFFFF", relief="flat", padx=10, pady=5, command=self.root.quit)
        self.boton_salir.pack(pady=15)

        self.mostrar_bienvenida()

    def mostrar_bienvenida(self):
        self.frame_juego.pack_forget()
        self.frame_bienvenida.pack(fill="both", expand=True)
        self.entry_jugador.delete(0, tk.END)  # Limpiar el campo de nombre
        self.idioma.set("Español")  # Restablecer idioma por defecto

    def iniciar_juego(self):
        self.jugador = self.entry_jugador.get().strip() or "Jugador"
        self.idioma_juego = self.idioma.get()
        self.palabra = obtener_palabra_aleatoria(self.idioma_juego)
        self.letras_adivinadas = set()
        self.intentos_restantes = 6
        self.intentos_por_letra = Counter()
        self.frame_bienvenida.pack_forget()
        self.frame_juego.pack(fill="both", expand=True)

        # Limpiar widgets del juego anteriores
        for widget in self.frame_juego.winfo_children():
            widget.destroy()

        self.canvas = tk.Canvas(self.frame_juego, width=300, height=300, bg="#f5f5f5", borderwidth=5, relief="ridge", highlightbackground="#0d47a1")
        self.canvas.pack(pady=20)
        self.dibujar_ahorcado()
        self.label_palabra = tk.Label(self.frame_juego, text="", font=("Segoe UI", 22, "bold"), bg="#a8d4fa", fg="#0d47a1")
        self.label_palabra.pack(pady=20)
        self.label_intentos = tk.Label(self.frame_juego, text=f"Intentos restantes: {self.intentos_restantes}", font=("Segoe UI", 16, "bold"), bg="#a8d4fa", fg="#0d47a1")
        self.label_intentos.pack(pady=15)
        self.label_letras = tk.Label(self.frame_juego, text="Letras intentadas: Ninguna", font=("Segoe UI", 14), bg="#a8d4fa", fg="#0d47a1")
        self.label_letras.pack(pady=15)
        self.entry_letra = tk.Entry(self.frame_juego, width=5, font=("Segoe UI", 14), relief="flat", bg="#e3f2fd", highlightthickness=1, highlightcolor="#0d47a1")
        self.entry_letra.pack(pady=15)
        self.entry_letra.bind("<Return>", lambda event: self.procesar_adivinanza())
        self.boton_adivinar = tk.Button(self.frame_juego, text="Adivinar", font=("Segoe UI", 14), bg="#2196F3", fg="#FFFFFF", activebackground="#1976D2", activeforeground="#FFFFFF", relief="flat", padx=10, pady=5, command=self.procesar_adivinanza)
        self.boton_adivinar.pack(pady=10)
        self.boton_reiniciar = tk.Button(self.frame_juego, text="Jugar de nuevo", font=("Segoe UI", 14), bg="#0288D1", fg="#FFFFFF", activebackground="#0277BD", activeforeground="#FFFFFF", relief="flat", padx=10, pady=5, command=self.reiniciar_juego)
        self.boton_reiniciar.pack(pady=10)
        self.boton_volver = tk.Button(self.frame_juego, text="Volver al Menú", font=("Segoe UI", 14), bg="#607D8B", fg="#FFFFFF", activebackground="#546E7A", activeforeground="#FFFFFF", relief="flat", padx=10, pady=5, command=self.mostrar_bienvenida)
        self.boton_volver.pack(pady=10)
        self.actualizar_interfaz()

    def dibujar_ahorcado(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, 300, 300, fill="#e3f2fd", outline="")
        self.canvas.create_rectangle(70, 270, 80, 200, fill="#8B4513", outline="#5D2E0D")
        self.canvas.create_rectangle(150, 270, 160, 75, fill="#8B4513", outline="#5D2E0D")
        self.canvas.create_rectangle(150, 75, 210, 85, fill="#8B4513", outline="#5D2E0D")
        self.canvas.create_line(210, 80, 210, 105, width=4, fill="#654321")
        fallos = 6 - self.intentos_restantes
        if fallos >= 1:
            self.canvas.create_oval(195, 105, 225, 135, outline="#0d47a1", width=2)
            self.canvas.create_oval(200, 110, 205, 115, fill="black")
            self.canvas.create_oval(215, 110, 220, 115, fill="black")
        if fallos >= 2:
            self.canvas.create_line(210, 135, 210, 195, width=3, fill="#0d47a1")
        if fallos >= 3:
            self.canvas.create_line(210, 135, 180, 165, width=3, fill="#0d47a1")
        if fallos >= 4:
            self.canvas.create_line(210, 135, 240, 165, width=3, fill="#0d47a1")
        if fallos >= 5:
            self.canvas.create_line(210, 195, 180, 225, width=3, fill="#0d47a1")
        if fallos >= 6:
            self.canvas.create_line(210, 195, 240, 225, width=3, fill="#0d47a1")
            self.canvas.create_line(200, 125, 210, 130, 220, 125, width=2, fill="red")

    def procesar_adivinanza(self):
        letra = self.entry_letra.get().lower()
        self.entry_letra.delete(0, tk.END)
        if not letra.isalpha() or len(letra) != 1:
            if self.sonido_error:
                self.sonido_error.play()
            messagebox.showwarning("Entrada inválida", "Por favor, ingresa una sola letra válida.")
            return
        self.intentos_por_letra[letra] += 1
        if letra in self.letras_adivinadas:
            if self.sonido_error:
                self.sonido_error.play()
            messagebox.showinfo("Repetida", "Ya intentaste esa letra. Prueba otra.")
            return
        self.letras_adivinadas.add(letra)
        if letra in self.palabra:
            if self.sonido_acierto:
                self.sonido_acierto.play()
            messagebox.showinfo("¡Acierto!", "La letra está en la palabra.")
            self.label_palabra.configure(fg="green")
            self.root.after(200, lambda: self.label_palabra.configure(fg="#0d47a1"))
        else:
            self.intentos_restantes -= 1
            if self.sonido_error:
                self.sonido_error.play()
            messagebox.showerror("Error", "La letra no está en la palabra.")
            self.dibujar_ahorcado()
        self.actualizar_interfaz()
        if all(letra in self.letras_adivinadas for letra in self.palabra):
            if self.sonido_victoria:
                self.sonido_victoria.play()
            guardar_puntuacion(self.jugador, self.palabra, True, self.idioma_juego)
            messagebox.showinfo("¡Victoria!", f"¡Felicidades! Adivinaste la palabra: {self.palabra}\nEstadísticas: {dict(self.intentos_por_letra)}")
            self.boton_adivinar.config(state="disabled")
            self.entry_letra.config(state="disabled")
        elif self.intentos_restantes == 0:
            if self.sonido_derrota:
                self.sonido_derrota.play()
            guardar_puntuacion(self.jugador, self.palabra, False, self.idioma_juego)
            messagebox.showerror("Derrota", f"¡Perdiste! La palabra era: {self.palabra}\nEstadísticas: {dict(self.intentos_por_letra)}")
            self.boton_adivinar.config(state="disabled")
            self.entry_letra.config(state="disabled")
            self.label_palabra.config(text=self.palabra)

    def actualizar_interfaz(self):
        self.label_palabra.config(text=mostrar_palabra(self.palabra, self.letras_adivinadas))
        self.label_intentos.config(text=f"Intentos restantes: {self.intentos_restantes}")
        self.label_letras.config(text=f"Letras intentadas: {', '.join(sorted(self.letras_adivinadas)) or 'Ninguna'}")

    def reiniciar_juego(self):
        self.palabra = obtener_palabra_aleatoria(self.idioma_juego)
        self.letras_adivinadas = set()
        self.intentos_restantes = 6
        self.intentos_por_letra = Counter()
        self.boton_adivinar.config(state="normal")
        self.entry_letra.config(state="normal")
        self.dibujar_ahorcado()
        self.actualizar_interfaz()

async def main():
    configurar_base_datos()
    root = tk.Tk()
    juego = JuegoAhorcado(root)
    root.mainloop()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())