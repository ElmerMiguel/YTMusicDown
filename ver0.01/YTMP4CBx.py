# pip install pytube yt-dlp
# pyinstaller --onefile --icon=yticonn.ico --noconsole --add-data "C:\ffmpeg\bin\ffmpeg.exe;." --add-data "C:\ffmpeg\bin\ffplay.exe;." --add-data "C:\ffmpeg\bin\ffprobe.exe;." YTMP4CBx.py

# noUnico
# pyinstaller --icon=yticonn.ico --noconsole --add-data "C:\ffmpeg\bin\ffmpeg.exe;." --add-data "C:\ffmpeg\bin\ffplay.exe;." --add-data "C:\ffmpeg\bin\ffprobe.exe;." YTMP4CBx.py


import os
import re
import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

# Ruta a los binarios de FFmpeg
FFMPEG_LOCATION = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')

# Lista de caracteres no permitidos en nombres de archivos y directorios en Windows
INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1F]'

def sanitize_filename(filename):
    """Elimina o reemplaza los caracteres no permitidos en los nombres de archivos y directorios de Windows."""
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

def descargar_playlist(url, download_dir, quality, progress_var, status_var):
    try:
        nombre_playlist, nombre_artista = obtener_info_playlist(url)
        nombre_carpeta = f"{nombre_artista} - {nombre_playlist}"
        nombre_carpeta = sanitize_filename(nombre_carpeta)
        status_var.set(f"Descargando playlist: {nombre_carpeta}")
        
        full_download_dir = os.path.join(download_dir, nombre_carpeta)
        if not os.path.exists(full_download_dir):
            os.makedirs(full_download_dir)
        
        # Formato basado en la calidad seleccionada
        format_string = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/mp4'
        
        ydl_opts = {
            'format': format_string,
            'outtmpl': os.path.join(full_download_dir, '%(playlist_index)02d - %(title)s.%(ext)s'),
            'ffmpeg_location': FFMPEG_LOCATION, # parte de la localizacion de ffmpg al compilar windows
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'progress_hooks': [lambda d: progress_callback(d, progress_var, status_var)],
            'cleanup': True,  # Eliminar archivos temporales después de la combinación
            'ignoreerrors': True, # Ignorar errores y continuar con la siguiente descarga
            'geo_bypass': True, # Intentar eludir restricciones geográficas
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
        messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")

def progress_callback(d, progress_var, status_var):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        if total_bytes:
            progress = float(d['downloaded_bytes'] / total_bytes) * 100
            progress_var.set(progress)
            status_var.set(f"Descargando: {d['filename']}")
        else:
            status_var.set("Calculando tamaño del archivo...")

def seleccionar_carpeta():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_var.set(folder_selected)

def iniciar_descarga():
    url = url_entry.get()
    download_dir = folder_var.get()
    quality = quality_combobox.get()
    if url and download_dir and quality:
        progress_var.set(0)
        status_var.set("Iniciando descarga...")
        threading.Thread(target=descargar_playlist, args=(url, download_dir, quality, progress_var, status_var), daemon=True).start()
    else:
        messagebox.showwarning("Advertencia", "Por favor, ingresa una URL válida, selecciona una carpeta de destino y una calidad de video.")

# Crear la ventana principal
root = tk.Tk()
root.title("Descargador de Playlist de YouTube")
root.geometry("400x300")
root.configure(bg="#161526")

# Establecer el estilo
style = ttk.Style()
style.configure("TLabel", background="#161526", foreground="#F2F2F2")
style.configure("TButton", background="#8091F2", foreground="#161526")
style.configure("TEntry", background="#454C73", foreground="#1D1D1E", fieldbackground="#454C73")
style.configure("TCombobox", fieldbackground="#454C73", background="#454C73", foreground="#F2F2F2")
style.configure("TProgressbar", troughcolor="#454C73", background="#8091F2")

# Establecer el icono de la ventana principal
# root.iconbitmap('C:\\Users\\Elmer Mekel\\yticon\\yticon.ico')

# Crear y colocar los widgets
ttk.Label(root, text="Descargador de Playlist de YouTube - por ElmerMiguel", style="TLabel").pack(pady=5)

url_label = ttk.Label(root, text="URL de la playlist:", style="TLabel")
url_label.pack(pady=5)

url_entry = ttk.Entry(root, width=50, style="TEntry")
url_entry.pack(pady=5)

folder_var = tk.StringVar()
folder_label = ttk.Label(root, text="Carpeta de destino:", style="TLabel")
folder_label.pack(pady=5)

folder_frame = ttk.Frame(root)
folder_frame.pack(fill=tk.X, padx=20)

folder_entry = ttk.Entry(folder_frame, textvariable=folder_var, width=40, style="TEntry")
folder_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

folder_button = ttk.Button(folder_frame, text="Seleccionar", command=seleccionar_carpeta, style="TButton")
folder_button.pack(side=tk.RIGHT)

quality_label = ttk.Label(root, text="Calidad del video:", style="TLabel")
quality_label.pack(pady=5)

quality_combobox = ttk.Combobox(root, values=["144", "240", "360", "480", "720", "1080"], style="TCombobox")
quality_combobox.pack(pady=5)

download_button = ttk.Button(root, text="Descargar", command=iniciar_descarga, style="TButton")
download_button.pack(pady=10)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, style="TProgressbar")
progress_bar.pack(pady=5, fill=tk.X, padx=20)

status_var = tk.StringVar()
status_var.set("Esperando URL...")
status_label = ttk.Label(root, textvariable=status_var, style="TLabel")
status_label.pack(pady=5)

# Iniciar el loop principal
root.mainloop()
