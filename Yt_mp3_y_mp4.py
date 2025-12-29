import os
import re
import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

# Ruta de ffmpeg para Windows
# Se busca en la carpeta del script. Si no existe, yt-dlp lo buscará en el PATH del sistema.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_LOCATION = os.path.join(BASE_DIR, 'ffmpeg.exe')
INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1F]'

cookies_path = None

def sanitize_filename(filename):
    """Elimina o reemplaza caracteres no permitidos en nombres de archivos."""
    return re.sub(INVALID_CHARS, '_', filename)

def obtener_info_playlist(url):
    """Obtiene información básica de la playlist."""
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        nombre_playlist = info_dict.get('title', 'Playlist')
        nombre_artista = 'Artista'
        if 'entries' in info_dict and len(info_dict['entries']) > 0:
            first_entry = info_dict['entries'][0]
            if first_entry:
                nombre_artista = first_entry.get('uploader') or first_entry.get('artist') or 'Varios'
        return nombre_playlist, nombre_artista

def descargar_playlist(url, download_dir, format_type, progress_var, status_var):
    """Descarga y une audio/video automáticamente."""
    try:
        nombre_playlist, nombre_artista = obtener_info_playlist(url)
        nombre_carpeta = sanitize_filename(f"{nombre_artista} - {nombre_playlist}")
        status_var.set(f"Preparando: {nombre_carpeta}")

        full_download_dir = os.path.join(download_dir, nombre_carpeta)
        if not os.path.exists(full_download_dir):
            os.makedirs(full_download_dir)

        # Configuración base común
        ydl_opts = {
            'outtmpl': os.path.join(full_download_dir, '%(playlist_index)02d - %(title)s.%(ext)s'),
            'progress_hooks': [lambda d: progress_callback(d, progress_var, status_var)],
            'ignoreerrors': True,
            'geo_bypass': True,
            'cookiefile': cookies_path if cookies_path else None,
        }

        # Si el ejecutable de FFmpeg existe en la carpeta, se lo indicamos a yt-dlp
        if os.path.exists(FFMPEG_LOCATION):
            ydl_opts['ffmpeg_location'] = FFMPEG_LOCATION

        if format_type == "MP3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # Configuración para MP4 (Video + Audio unido)
            quality = format_type.split(" ")[1][1:-1]  # Extrae '480', '720', etc.
            ydl_opts.update({
                # Busca el mejor video hasta la calidad elegida + el mejor audio disponible
                'format': f'bestvideo[height<={quality}]+bestaudio/best',
                # Fuerza a que el contenedor final sea MP4
                'merge_output_format': 'mp4',
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        status_var.set("Descarga completa.")
        messagebox.showinfo("Éxito", "¡Proceso finalizado con éxito!")
    except Exception as e:
        status_var.set("Error en la descarga.")
        messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")

def progress_callback(d, progress_var, status_var):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        if total:
            p = (d['downloaded_bytes'] / total) * 100
            progress_var.set(p)
            status_var.set(f"Descargando: {int(p)}%")
    elif d['status'] == 'finished':
        status_var.set("Uniendo archivos (Merge)... por favor espera.")

def seleccionar_carpeta():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def importar_cookies():
    global cookies_path
    file_selected = filedialog.askopenfilename(filetypes=[("Cookies file", "*.txt")])
    if file_selected:
        cookies_path = file_selected
        cookies_label.config(text=f"Cookies: {os.path.basename(cookies_path)}")

def iniciar_descarga():
    url = url_entry.get()
    download_dir = folder_var.get()
    format_type = format_combobox.get()
    if url and download_dir:
        progress_var.set(0)
        threading.Thread(target=descargar_playlist, args=(url, download_dir, format_type, progress_var, status_var), daemon=True).start()
    else:
        messagebox.showwarning("Atención", "Completa todos los campos.")

# --- Interfaz Gráfica ---
root = tk.Tk()
root.title("YT Download Fixer")
root.geometry("450x450")

ttk.Label(root, text="Descargador MP3/MP4 (Auto-Merge)", font=("Arial", 10, "bold")).pack(pady=10)

ttk.Label(root, text="URL de la Playlist o Video:").pack()
url_entry = ttk.Entry(root, width=50)
url_entry.pack(pady=5)

folder_var = tk.StringVar()
ttk.Button(root, text="Seleccionar Carpeta Destino", command=seleccionar_carpeta).pack(pady=5)
ttk.Entry(root, textvariable=folder_var, width=50, state="readonly").pack()

ttk.Button(root, text="Cargar cookies.txt (Opcional)", command=importar_cookies).pack(pady=10)
cookies_label = ttk.Label(root, text="Sin cookies")
cookies_label.pack()

ttk.Label(root, text="Formato y Calidad:").pack(pady=5)
format_combobox = ttk.Combobox(root, values=["MP3", "MP4 (480p)", "MP4 (720p)", "MP4 (1080p)"], state="readonly")
format_combobox.current(0)
format_combobox.pack()

ttk.Button(root, text="INICIAR DESCARGA", command=iniciar_descarga).pack(pady=20)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(fill=tk.X, padx=30)

status_var = tk.StringVar(value="Listo para descargar")
ttk.Label(root, textvariable=status_var, wraplength=400).pack(pady=10)

root.mainloop()