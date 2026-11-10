# DownloaderYT.py
import yt_dlp
import os
import sys
import time
import re
import subprocess
from mutagen.id3 import ID3, TIT2, TPE1
from Downloader import obtener_ruta_config, obtener_ultima_carpeta, obtener_ultimo_formato

def obtener_ruta_ffmpeg():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(".")

class MusicDownloaderYT:
    def __init__(self):
        pass

    def search_songs(self, url):
        """Extrae metadatos de un video, playlist normal o radio de YouTube."""
        
        es_radio = "list=RD" in url or "start_radio=1" in url
        es_playlist_real = "list=" in url and not es_radio
        
        songs = []
        
        # ==========================================
        # CASO 1: PLAYLIST REAL (Extraer todos los videos)
        # ==========================================
        if es_playlist_real:
            print("Detectada Playlist Real de YouTube. Extrayendo todos los videos...")
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extract_flat': True,
                'ignoreerrors': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if not isinstance(info, dict):
                        raise ValueError("YouTube no devolvió información de la playlist.")
                    if 'entries' in info:
                        for entry in info['entries'] or ():
                            if entry is None: continue
                            
                            titulo = entry.get('title', 'Desconocido')
                            artista = entry.get('uploader', 'Desconocido')
                            
                            # Limpieza del " - Topic"
                            if artista.endswith(" - Topic"):
                                artista = artista[:-8]

                            duration = entry.get('duration', 0) or 0
                            video_id = entry.get('id')
                            if not video_id:
                                continue
                            thumbnail = entry.get('thumbnail')
                            if not thumbnail and video_id:
                                thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                            
                            songs.append({
                                'name': titulo, # Título original del video
                                'artist': artista, # Nombre del canal
                                'url': f"https://www.youtube.com/watch?v={video_id}",
                                'album': 'YouTube', # Sin álbum real
                                'duration_ms': int(duration) * 1000,
                                'duration_str': time.strftime('%M:%S', time.gmtime(int(duration))),
                                'year': 'Desconocido',
                                'cover_url': thumbnail
                            })
                    return songs
            except Exception as e:
                print(f"Error obteniendo metadatos de Playlist: {e}")
                raise RuntimeError(f"No se pudo cargar la playlist de YouTube: {e}") from e

        # ==========================================
        # CASO 2: RADIO O VIDEO INDIVIDUAL
        # ==========================================
        else:
            print("Detectada Radio o Video Individual. Extrayendo solo este video...")
            match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
            if not match:
                return []
            
            video_id = match.group(1)
            url_limpia = f"https://www.youtube.com/watch?v={video_id}"
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'noplaylist': True,
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url_limpia, download=False)
                    
                    titulo = info.get('title', 'Desconocido')
                    artista = info.get('uploader', 'Desconocido')
                    
                    if artista.endswith(" - Topic"):
                        artista = artista[:-8]

                    duracion = info.get('duration', 0) or 0
                    upload_date = info.get('upload_date', '')
                    year = "Desconocido"
                    if upload_date and isinstance(upload_date, str) and len(upload_date) >= 4:
                        year = upload_date[:4]

                    thumbnail = info.get('thumbnail')
                    if not thumbnail:
                        thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                    return [{
                        'name': titulo,
                        'artist': artista,
                        'url': url_limpia,
                        'album': 'YouTube',
                        'duration_ms': int(duracion) * 1000,
                        'duration_str': time.strftime('%M:%S', time.gmtime(int(duracion))),
                        'year': year,
                        'cover_url': thumbnail
                    }]
            except Exception as e:
                print(f"Error obteniendo metadatos de YouTube: {e}")
                raise RuntimeError(f"No se pudo cargar el video de YouTube: {e}") from e

    def download_song(self, song_dict, formato, carpeta_destino):
        """Descarga el audio de YouTube y le inyecta título y artista."""
        self.last_error = None
        try:
            # El nombre del archivo será exactamente el título del video
            safe_title = "".join([c for c in song_dict['name'] if c.isalpha() or c.isdigit() or c in ' -_,']).rstrip()
            filename = f"{safe_title}.{formato}"
            output_path = os.path.join(carpeta_destino, filename)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                return output_path

            temp_download_path = os.path.join(carpeta_destino, f"tmp_{safe_title}")

            directorio_ffmpeg = obtener_ruta_ffmpeg()

            # 1. Descargar solo el audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_download_path,
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'ffmpeg_location': directorio_ffmpeg,
                'retries': 3,
                'fragment_retries': 3,
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': formato,
                        'preferredquality': '192',
                    }
                ]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([song_dict['url']])

            downloaded_file = f"{temp_download_path}.{formato}"
            if not os.path.exists(downloaded_file):
                raise Exception("El archivo no se descargó correctamente.")

            # 2. Inyectar metadatos de texto (Título y Artista) usando mutagen
            # Esto solo funciona para MP3, para M4A/FLAC tendríamos que usar ffmpeg de nuevo, 
            # pero para simplificar, usaremos ffmpeg.
            
            ffmpeg_exe = os.path.join(directorio_ffmpeg, "ffmpeg.exe" if os.name == 'nt' else "ffmpeg")
            temp_output = os.path.join(carpeta_destino, f"final_{safe_title}.{formato}")
            
            comando = [
                ffmpeg_exe, '-y', '-i', downloaded_file,
                '-metadata', f'title={song_dict["name"]}',
                '-metadata', f'artist={song_dict["artist"]}',
                # Sin metadatos de álbum ni portada
                '-codec:a', 'copy', temp_output
            ]
            
            subprocess.run(comando, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            os.remove(downloaded_file)
            os.replace(temp_output, output_path)

            return output_path
        except Exception as e:
            self.last_error = str(e)
            print(f"Error al descargar desde YouTube {song_dict['name']}: {e}")
            if 'temp_download_path' in locals() and os.path.exists(f"{temp_download_path}.{formato}"):
                os.remove(f"{temp_download_path}.{formato}")
            return None