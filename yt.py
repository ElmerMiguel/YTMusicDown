import os
import re
import sys
import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

# Ruta de ffmpeg para Windows (cuando empaquetes con PyInstaller)
FFMPEG_LOCATION = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1F]'

cookies_path = None  # ruta al archivo cookies.txt

def sanitize_filename(filename):
    return re.sub(INVALID_CHARS, '_', filename)

def obtener_info_playlist(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': True,
        'force_generic_extractor': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        nombre_playlist = info_dict.get('title', 'Playlist')
        nombre_artista = 'Artista'
        if 'entries' in info_dict and len(info_dict['entries']) > 0:
            first_entry = info_dict['entries'][0]
            if 'artist' in first_entry:
                nombre_artista = first_entry['artist']
            elif 'uploader' in first_entry:
                nombre_artista = first_entry['uploader']
            elif 'channel' in first_entry:
                nombre_artista = first_entry['channel']
        return nombre_playlist, nombre_artista

def descargar_playlist(url, download_dir, progress_var, status_var):
    try:
        nombre_playlist, nombre_artista = obtener_info_playlist(url)
        nombre_carpeta = f"{nombre_artista} - {nombre_playlist}"
        nombre_carpeta = sanitize_filename(nombre_carpeta)
        status_var.set(f"Descargando playlist: {nombre_carpeta}")

        full_download_dir = os.path.join(download_dir, nombre_carpeta)
        if not os.path.exists(full_download_dir):
            os.makedirs(full_download_dir)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(full_download_dir, '%(playlist_index)02d - %(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [lambda d: progress_callback(d, progress_var, status_var)],
            'noplaylist': False,
            'merge_output_format': 'mp3',
            'hls_use_mpegts': True,
            'geo_bypass': True,
            'ignoreerrors': True,
            'retries': 10,
            'verbose': True,
            'cookiefile': cookies_path if cookies_path else None,
            'force_generic_extractor': False,
            'extract_flat': False,
            'js_executables': ['/opt/node-v22.21.0-linux-x64/bin/node'],  # Forzar Node.js
            'remote_components': ['ejs:npm', 'ejs:github'],  # Habilitar componentes remotos
            'compat_opts': ['no-youtube-unavailable-videos'],  # Evitar videos no disponibles
            'js_runtimes': {'node': {'executable': '/opt/node-v22.21.0-linux-x64/bin/node'}},  # Correct Node.js runtime format
            'hls_prefer_native': True,  # Use native HLS downloader
            'fragment_retries': 20,  # Increase fragment retries
        }

        # Solo en Windows se añade la ruta empaquetada de ffmpeg
        if sys.platform.startswith("win"):
            ydl_opts['ffmpeg_location'] = FFMPEG_LOCATION

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        status_var.set("Descarga completa.")
        messagebox.showinfo("Éxito", "Descarga completada con éxito!")
    except yt_dlp.utils.DownloadError as e:
        status_var.set("Error en la descarga.")
        messagebox.showerror("Error", f"Error de descarga: {str(e)}")
    except Exception as e:
        status_var.set("Error en la descarga.")
        messagebox.showerror("Error", f"Ocurrió un error inesperado: {str(e)}")

def progress_callback(d, progress_var, status_var):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        if total_bytes:
            progress = float(d['downloaded_bytes'] / total_bytes) * 100
            progress_var.set(progress)
            status_var.set(f"Descargando: {d.get('filename', 'archivo')}")
        elif d.get('fragment_count'):
            # Para streams HLS (m3u8)
            current = d.get('fragment_index', 0)
            total = d['fragment_count']
            progress = (current / total) * 100
            progress_var.set(progress)
            status_var.set(f"Descargando fragmento {current}/{total}")
        else:
            status_var.set("Calculando tamaño del archivo...")


def seleccionar_carpeta():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_var.set(folder_selected)

def importar_cookies():
    global cookies_path
    file_selected = filedialog.askopenfilename(filetypes=[("Cookies file", "*.txt")])
    if file_selected:
        cookies_path = file_selected
        cookies_label.config(text=f"Cookies cargadas: {os.path.basename(cookies_path)}")

def iniciar_descarga():
    url = url_entry.get()
    download_dir = folder_var.get()
    if url and download_dir:
        progress_var.set(0)
        status_var.set("Iniciando descarga...")
        threading.Thread(target=descargar_playlist, args=(url, download_dir, progress_var, status_var), daemon=True).start()
    else:
        messagebox.showwarning("Advertencia", "Por favor, ingresa una URL válida y selecciona una carpeta de destino.")

# GUI
root = tk.Tk()
root.title("Descargador de Playlist de YouTube Music")
root.geometry("400x300")

ttk.Label(root, text="Descargador de álbum YTMusic - por ElmerMiguel").pack(pady=5)

url_label = ttk.Label(root, text="URL de la playlist:")
url_label.pack(pady=5)

url_entry = ttk.Entry(root, width=50)
url_entry.pack(pady=5)

folder_var = tk.StringVar()
folder_label = ttk.Label(root, text="Carpeta de destino:")
folder_label.pack(pady=5)

folder_frame = ttk.Frame(root)
folder_frame.pack(fill=tk.X, padx=20)

folder_entry = ttk.Entry(folder_frame, textvariable=folder_var, width=40)
folder_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

folder_button = ttk.Button(folder_frame, text="Seleccionar", command=seleccionar_carpeta)
folder_button.pack(side=tk.RIGHT)

ttk.Button(root, text="Importar cookies.txt", command=importar_cookies).pack(pady=5)
cookies_label = ttk.Label(root, text="Sin cookies cargadas")
cookies_label.pack(pady=2)

download_button = ttk.Button(root, text="Descargar", command=iniciar_descarga)
download_button.pack(pady=10)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(pady=5, fill=tk.X, padx=20)

status_var = tk.StringVar()
status_var.set("Esperando URL...")
status_label = ttk.Label(root, textvariable=status_var)
status_label.pack(pady=5)

root.mainloop()

