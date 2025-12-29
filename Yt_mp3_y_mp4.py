import os
import re
import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

# Ruta de ffmpeg para Windows (cuando empaquetes con PyInstaller)
FFMPEG_LOCATION = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1F]'

cookies_path = None  # Ruta al archivo cookies.txt

def sanitize_filename(filename):
    """Elimina o reemplaza caracteres no permitidos en nombres de archivos y directorios."""
    return re.sub(INVALID_CHARS, '_', filename)

def obtener_info_playlist(url):
    """Obtiene información básica de la playlist, como el nombre y el artista."""
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

def descargar_playlist(url, download_dir, format_type, progress_var, status_var):
    """Descarga la playlist en el formato y calidad seleccionados."""
    try:
        nombre_playlist, nombre_artista = obtener_info_playlist(url)
        nombre_carpeta = f"{nombre_artista} - {nombre_playlist}"
        nombre_carpeta = sanitize_filename(nombre_carpeta)
        status_var.set(f"Descargando playlist: {nombre_carpeta}")

        full_download_dir = os.path.join(download_dir, nombre_carpeta)
        if not os.path.exists(full_download_dir):
            os.makedirs(full_download_dir)

        # Configuración para MP3
        if format_type == "MP3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(full_download_dir, '%(playlist_index)02d - %(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'merge_output_format': 'mp3',
                'progress_hooks': [lambda d: progress_callback(d, progress_var, status_var)],
                'hls_use_mpegts': True,
                'geo_bypass': True,
                'ignoreerrors': True,
                'retries': 10,
                'verbose': True,
                'cookiefile': cookies_path if cookies_path else None,
                'js_executables': ['node'],  # Usar Node.js desde el PATH
                'remote_components': ['ejs:npm', 'ejs:github'],  # Habilitar componentes remotos
                'compat_opts': ['no-youtube-unavailable-videos'],  # Evitar videos no disponibles
                'js_runtimes': {'node': {'executable': 'node'}},  # Use 'node' from PATH
                'fragment_retries': 20,  # Aumentar reintentos de fragmentos
            }
        # Configuración para MP4 con calidad específica
        else:
            quality = format_type.split(" ")[1][1:-1]  # Extraer la calidad (e.g., "480", "720")
            format_string = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/mp4'
            ydl_opts = {
                'format': format_string,
                'outtmpl': os.path.join(full_download_dir, '%(playlist_index)02d - %(title)s.%(ext)s'),
                'ffmpeg_location': FFMPEG_LOCATION,  # Ruta de ffmpeg para Windows
                'merge_output_format': 'mp4',
                'progress_hooks': [lambda d: progress_callback(d, progress_var, status_var)],
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',  # Asegurar que el archivo final sea MP4
                }],
                'cleanup': True,  # Eliminar archivos temporales después de la combinación
                'ignoreerrors': True,  # Ignorar errores y continuar con la siguiente descarga
                'geo_bypass': True,  # Intentar eludir restricciones geográficas
            }

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
    """Actualiza la barra de progreso y el estado durante la descarga."""
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
    """Permite al usuario seleccionar una carpeta de destino."""
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_var.set(folder_selected)

def importar_cookies():
    """Permite al usuario importar un archivo de cookies."""
    global cookies_path
    file_selected = filedialog.askopenfilename(filetypes=[("Cookies file", "*.txt")])
    if file_selected:
        cookies_path = file_selected
        cookies_label.config(text=f"Cookies cargadas: {os.path.basename(cookies_path)}")

def iniciar_descarga():
    """Inicia la descarga en un hilo separado."""
    url = url_entry.get()
    download_dir = folder_var.get()
    format_type = format_combobox.get()
    if url and download_dir and format_type:
        progress_var.set(0)
        status_var.set("Iniciando descarga...")
        threading.Thread(target=descargar_playlist, args=(url, download_dir, format_type, progress_var, status_var), daemon=True).start()
    else:
        messagebox.showwarning("Advertencia", "Por favor, ingresa una URL válida, selecciona una carpeta de destino y un formato.")

# GUI
root = tk.Tk()
root.title("Descargador de Playlist de YouTube Music")
root.geometry("400x400")

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

format_label = ttk.Label(root, text="Formato de descarga:")
format_label.pack(pady=5)

format_combobox = ttk.Combobox(root, values=["MP3", "MP4 (480p)", "MP4 (720p)", "MP4 (1080p)"], state="readonly")
format_combobox.pack(pady=5)
format_combobox.set("MP3")  # Valor predeterminado

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