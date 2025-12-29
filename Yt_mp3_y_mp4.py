import os
import re
import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

# ============ CONFIGURACIÓN DE ESTILO (Paleta Biblioteca Mágica) ============
BG_COLOR = "#e6f0ff"        
TITLE_COLOR = "#2a2a72"     
BUTTON_COLOR = "#4a90e2"    
ACCENT_COLOR = "#1e6bbd"    
CARD_BG = "#ffffff"         

# FUENTES
FONT_TITLE_LARGE = ("Georgia", 28, "bold")
FONT_TITLE_MEDIUM = ("Arial", 12, "bold")
FONT_LABEL = ("Arial", 11)
FONT_BUTTON = ("Arial", 11, "bold")
FONT_SMALL = ("Arial", 9)

INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1F]'
cookies_path = None

# ============ LÓGICA DE DESCARGA ============

def sanitize_filename(filename):
    return re.sub(INVALID_CHARS, '_', filename)

def obtener_info_playlist(url):
    ydl_opts = {'quiet': True, 'skip_download': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        nombre_playlist = info_dict.get('title', 'Playlist')
        nombre_artista = 'Artista'
        if 'entries' in info_dict and len(info_dict['entries']) > 0:
            first_entry = info_dict['entries'][0]
            if first_entry:
                nombre_artista = first_entry.get('uploader') or first_entry.get('artist') or 'Varios'
        return nombre_playlist, nombre_artista

def descargar_playlist(url, download_dir, format_type, progress_var, status_var, btn_control):
    try:
        btn_control("disabled")
        status_var.set("Analizando enlace...")
        
        nombre_playlist, nombre_artista = obtener_info_playlist(url)
        nombre_carpeta = sanitize_filename(f"{nombre_artista} - {nombre_playlist}")
        
        full_download_dir = os.path.join(download_dir, nombre_carpeta)
        if not os.path.exists(full_download_dir):
            os.makedirs(full_download_dir)

        ydl_opts = {
            'outtmpl': os.path.join(full_download_dir, '%(playlist_index)02d - %(title)s.%(ext)s'),
            'progress_hooks': [lambda d: progress_callback(d, progress_var, status_var)],
            'ignoreerrors': True,
            'geo_bypass': True,
            'cookiefile': cookies_path if cookies_path else None,
        }

        if format_type == "MP3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            })
        else:
            quality = format_type.split(" ")[1][1:-1]
            ydl_opts.update({
                'format': f'bestvideo[height<={quality}]+bestaudio/best',
                'merge_output_format': 'mp4',
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        status_var.set("¡Completado con éxito!")
        progress_var.set(100)
        messagebox.showinfo("Éxito", f"Archivos guardados en:\n{nombre_carpeta}")
    except Exception as e:
        status_var.set("Error detectado")
        messagebox.showerror("Error", str(e))
    finally:
        btn_control("normal")

def progress_callback(d, progress_var, status_var):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        if total:
            p = (d['downloaded_bytes'] / total) * 100
            progress_var.set(p)
            status_var.set(f"Descargando contenido... {int(p)}%")
    elif d['status'] == 'finished':
        status_var.set("Uniendo pistas de audio y video...")

# ============ INTERFAZ GRÁFICA ============

def seleccionar_carpeta():
    folder = filedialog.askdirectory()
    if folder: folder_var.set(folder)

def importar_cookies():
    global cookies_path
    file = filedialog.askopenfilename(filetypes=[("Archivo Cookies", "*.txt")])
    if file:
        cookies_path = file
        lbl_cookies.config(text=f"✓ Cookies: {os.path.basename(file)}", foreground=ACCENT_COLOR)

def ejecutar():
    url = ent_url.get()
    dest = folder_var.get()
    fmt = cmb_format.get()
    if url and dest:
        progress_var.set(0)
        threading.Thread(target=descargar_playlist, args=(url, dest, fmt, progress_var, status_var, lambda s: btn_run.config(state=s)), daemon=True).start()
    else:
        messagebox.showwarning("Campos vacíos", "Por favor ingresa la URL y la ruta de guardado.")

root = tk.Tk()
root.title("YT Downloader Ew")
root.geometry("700x600")
root.configure(bg=BG_COLOR)

style = ttk.Style()
style.theme_use('clam')

# Configuración de estilos
style.configure("TFrame", background=BG_COLOR)
style.configure("Card.TFrame", background=CARD_BG, relief="flat")
style.configure("TLabel", background=CARD_BG, foreground=TITLE_COLOR, font=FONT_LABEL)
style.configure("Header.TLabel", background=BG_COLOR, foreground=TITLE_COLOR, font=FONT_TITLE_LARGE)
style.configure("Status.TLabel", background=CARD_BG, foreground=ACCENT_COLOR, font=FONT_SMALL)
style.configure("Main.TButton", background=BUTTON_COLOR, foreground="white", font=FONT_BUTTON, borderwidth=0)
style.map("Main.TButton", background=[('active', '#357abd'), ('disabled', '#a0c4ff')])
style.configure("Horizontal.TProgressbar", background=BUTTON_COLOR, troughcolor=BG_COLOR, thickness=15)

# --- INICIALIZACIÓN DE VARIABLES DE CONTROL ---
# Deben estar antes de crear los widgets que las usan
folder_var = tk.StringVar(value=os.path.expanduser("~"))
progress_var = tk.DoubleVar(value=0)
status_var = tk.StringVar(value="Esperando instrucciones...")

# --- MAQUETACIÓN ---

header_label = ttk.Label(root, text="✨ YT Downloader Ew ✨", style="Header.TLabel", anchor="center")
header_label.pack(pady=(30, 20), fill=tk.X)

card = ttk.Frame(root, style="Card.TFrame", padding=40)
card.pack(padx=30, pady=10, fill=tk.BOTH, expand=True)

# URL
ttk.Label(card, text="URL del Video o Playlist:", font=FONT_TITLE_MEDIUM).pack(anchor="w")
ent_url = ttk.Entry(card, font=("Arial", 11))
ent_url.pack(fill=tk.X, pady=(5, 20))

# Directorio
ttk.Label(card, text="Directorio de descarga:", font=FONT_TITLE_MEDIUM).pack(anchor="w")
f_frame = ttk.Frame(card, style="Card.TFrame")
f_frame.pack(fill=tk.X, pady=(5, 20))

ent_folder = ttk.Entry(f_frame, textvariable=folder_var, font=("Arial", 10))
ent_folder.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
btn_folder = ttk.Button(f_frame, text="Explorar", command=seleccionar_carpeta)
btn_folder.pack(side=tk.RIGHT)

# Opciones
bottom_opts = ttk.Frame(card, style="Card.TFrame")
bottom_opts.pack(fill=tk.X, pady=10)

fmt_box = ttk.Frame(bottom_opts, style="Card.TFrame")
fmt_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
ttk.Label(fmt_box, text="Formato final:", font=FONT_TITLE_MEDIUM).pack(anchor="w")
cmb_format = ttk.Combobox(fmt_box, values=["MP3", "MP4 (480p)", "MP4 (720p)", "MP4 (1080p)"], state="readonly")
cmb_format.current(0)
cmb_format.pack(anchor="w", pady=5)

cook_box = ttk.Frame(bottom_opts, style="Card.TFrame")
cook_box.pack(side=tk.RIGHT, fill=tk.X)
ttk.Label(cook_box, text="Acceso Premium:", font=FONT_TITLE_MEDIUM).pack(anchor="w")
btn_cook = ttk.Button(cook_box, text="Importar Cookies.txt", command=importar_cookies)
btn_cook.pack(pady=5)
lbl_cookies = ttk.Label(cook_box, text="Sin cookies cargadas", font=FONT_SMALL, foreground="gray")
lbl_cookies.pack()

# Botón Ejecutar
btn_run = ttk.Button(card, text="DESCARGAR AHORA", style="Main.TButton", command=ejecutar, cursor="hand2")
btn_run.pack(fill=tk.X, pady=(20, 0), ipady=12)

# Barra de progreso y estado (Usando las variables ya definidas arriba)
pb = ttk.Progressbar(card, variable=progress_var, maximum=100, style="Horizontal.TProgressbar")
pb.pack(fill=tk.X, pady=(20, 5))

lbl_status = ttk.Label(card, textvariable=status_var, style="Status.TLabel", anchor="center")
lbl_status.pack(fill=tk.X)

root.mainloop()