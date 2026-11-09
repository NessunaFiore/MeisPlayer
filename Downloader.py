# Downloader.py
import spotipy
import os
import sys
import yt_dlp
import urllib.request
import syncedlyrics
import io
import subprocess
import time
import json # <--- NUEVO
from PIL import Image
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
from mutagen.id3 import ID3, USLT

REDIRECT_URI = "http://127.0.0.1:8080/callback"

def obtener_ruta_config():
    """Retorna la ruta del archivo config.json en la misma carpeta del script o exe."""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "config.json")

class MusicDownloader:
    def __init__(self):
        config_path = obtener_ruta_config()
        
        # Si no existe el archivo de config, lanzamos un error para que Main.py lo atrape
        if not os.path.exists(config_path):
            raise Exception("No se encontró el archivo de configuración.")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        CLIENT_ID = config.get("CLIENT_ID")
        CLIENT_SECRET = config.get("CLIENT_SECRET")

        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope="playlist-read-private"
        ))
        self.ytmusic = YTMusic()

    def search_songs(self, url):
        songs = []
        try:
            track_id = url.split("/track/")[-1].split("?")[0] if "/track/" in url else None
            playlist_id = url.split("/playlist/")[-1].split("?")[0] if "/playlist/" in url else None

            if playlist_id:
                results = self.sp.playlist_items(playlist_id)
                tracks = results['items']
                
                # --- PAUSA DE SEGURIDAD (EVITA BLOQUEO DE SPOTIFY) ---
                while results['next']:
                    time.sleep(1.5)  # Espera 1.5 segundos entre páginas de 100 canciones
                    results = self.sp.next(results)
                    tracks.extend(results['items'])
                # -----------------------------------------------------

                for item in tracks:
                    track = item.get('track') or item.get('item')
                    if track is None: continue
                    try:
                        duration_ms = track.get('duration_ms', 0)
                        duration_sec = duration_ms // 1000
                        mins, secs = divmod(duration_sec, 60)
                        duracion_str = f"{mins}:{secs:02d}"
                        album_info = track.get('album', {})
                        album_name = album_info.get('name', 'Desconocido')
                        release_date = album_info.get('release_date', '')
                        year = release_date[:4] if release_date else 'Desconocido'
                        images = album_info.get('images', [])
                        cover_url = images[0]['url'] if images else None

                        songs.append({
                            'name': track.get('name', 'Desconocido'),
                            'artist': track['artists'][0]['name'] if track.get('artists') else 'Desconocido',
                            'url': track['external_urls']['spotify'],
                            'album': album_name,
                            'duration_ms': duration_ms,
                            'duration_str': duracion_str,
                            'year': year,
                            'cover_url': cover_url
                        })
                    except (KeyError, IndexError, TypeError): continue

            elif track_id:
                track = self.sp.track(track_id)
                if track:
                    duration_ms = track.get('duration_ms', 0)
                    duration_sec = duration_ms // 1000
                    mins, secs = divmod(duration_sec, 60)
                    duracion_str = f"{mins}:{secs:02d}"
                    album_info = track.get('album', {})
                    album_name = album_info.get('name', 'Desconocido')
                    release_date = album_info.get('release_date', '')
                    year = release_date[:4] if release_date else 'Desconocido'
                    images = album_info.get('images', [])
                    cover_url = images[0]['url'] if images else None

                    songs.append({
                        'name': track['name'],
                        'artist': track['artists'][0]['name'],
                        'url': track['external_urls']['spotify'],
                        'album': album_name,
                        'duration_ms': duration_ms,
                        'duration_str': duracion_str,
                        'year': year,
                        'cover_url': cover_url
                    })
        except Exception as e:
            print(f"Error en la búsqueda: {e}")
        return songs

    def download_song(self, song_dict, formato, carpeta_destino):
        try:
            safe_title = "".join([c for c in song_dict['name'] if c.isalpha() or c.isdigit() or c in ' -_,']).rstrip()
            
            # --- EN CASO DE NOMBRES DUPLICADOS EN CANCIONES---
            filename = f"{safe_title}.{formato}"
            output_path = os.path.join(carpeta_destino, filename)
            
            # Si el archivo base ya existe, verificamos de quién es
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                try:
                    audio_existente = None
                    if formato == 'mp3':
                        from mutagen.mp3 import MP3
                        audio_existente = MP3(output_path)
                    elif formato == 'm4a':
                        from mutagen.mp4 import MP4
                        audio_existente = MP4(output_path)
                    elif formato == 'flac':
                        from mutagen.flac import FLAC
                        audio_existente = FLAC(output_path)

                    artista_existente = ""
                    if audio_existente and audio_existente.tags:
                        if formato == 'mp3':
                            artista_existente = str(audio_existente.tags.get('TPE1', ''))
                        elif formato == 'm4a':
                            artista_existente = audio_existente.tags.get('©ART', [''])[0]
                        elif formato == 'flac':
                            artista_existente = audio_existente.tags.get('artist', [''])[0]

                    # Si el artista es el mismo, saltamos la canción
                    if song_dict['artist'].lower() in artista_existente.lower():
                        return output_path
                    else:
                        # Si el artista es diferente, cambiamos el nombre a "Cancion - Artista"
                        safe_artist = "".join([c for c in song_dict['artist'] if c.isalpha() or c.isdigit() or c in ' -_,']).rstrip()
                        filename = f"{safe_title} - {safe_artist}.{formato}"
                        output_path = os.path.join(carpeta_destino, filename)
                        
                        # Si el archivo con "Cancion - Artista" ya existe, lo saltamos
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                            return output_path
                            
                        print(f"Artista diferente. Guardando como: {filename}")
                except Exception as e:
                    print(f"No se pudo leer los metadatos del archivo existente: {e}. Se procederá a descargar.")
            # -------------------------------------

            # --- LIMPIEZA DE ARCHIVOS TEMPORALES EN CASO DE CIERRE INESPERADO ---
            temp_download_path = os.path.join(carpeta_destino, f"tmp_{safe_title}")
            temp_output = os.path.join(carpeta_destino, f"final_{safe_title}.{formato}")
            temp_cover = os.path.join(carpeta_destino, f"tmp_cover_{safe_title}.jpg")
            
            for f in [f"{temp_download_path}.{formato}", temp_output, temp_cover]:
                if os.path.exists(f):
                    try: os.remove(f)
                    except: pass
            # -------------------------------------

            query = f"{song_dict['artist']} {song_dict['name']}"
            
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                directorio_ffmpeg = sys._MEIPASS
            else:
                directorio_ffmpeg = os.path.abspath(".")
            
            ffmpeg_exe = os.path.join(directorio_ffmpeg, "ffmpeg.exe" if os.name == 'nt' else "ffmpeg")

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': temp_download_path,
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
                'ffmpeg_location': directorio_ffmpeg,
                'retries': 3,
                'fragment_retries': 3,
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': formato, 'preferredquality': '192'}]
            }

            descarga_exitosa = False

            # --- 1ER INTENTO: BUSQUEDA EN YOUTUBE MUSIC ---
            try:
                search_results = self.ytmusic.search(query, filter="songs", limit=5)
                if search_results:
                    video_id = None
                    duracion_spotify = song_dict.get('duration_ms', 0) / 1000
                    
                    for result in search_results:
                        if 'duration_seconds' not in result: continue
                        if abs(result['duration_seconds'] - duracion_spotify) < 10:
                            video_id = result['videoId']
                            break
                    
                    if not video_id:
                        video_id = search_results[0]['videoId']

                    url_youtube = f"https://www.youtube.com/watch?v={video_id}"
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url_youtube])
                    
                    descarga_exitosa = True
            except Exception as e:
                print(f"Aviso: Fallo en YouTube Music para '{song_dict['name']}'. INTENTANDO DESCARGA DE FUENTE ALTERNATIVA")

            # --- 2DO INTENTO: BUSQUEDA EN YOUTUBE NORMAL ---
            if not descarga_exitosa:
                try:
                    query_rescate = f"{song_dict['artist']} - {song_dict['name']} lyrics"
                    url_rescate = f"ytsearch1:{query_rescate}"
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url_rescate])
                    
                    descarga_exitosa = True
                except Exception as e:
                    raise Exception(f"Falló la descarga en ambas fuentes: {e}")

            if not descarga_exitosa:
                raise Exception("No se pudo descargar el audio.")

            downloaded_file = f"{temp_download_path}.{formato}"

            if not os.path.exists(downloaded_file):
                raise Exception("El archivo no se descargó correctamente.")

            temp_cover_file = None
            if song_dict.get('cover_url') and formato != 'wav':
                try:
                    temp_cover_file = temp_cover
                    req = urllib.request.Request(song_dict['cover_url'], headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response:
                        img = Image.open(io.BytesIO(response.read())).convert('RGB')
                        img = img.resize((500, 500), Image.Resampling.LANCZOS)
                        img.save(temp_cover_file, format='JPEG', quality=95)
                except Exception as e:
                    print(f"Error preparando portada: {e}")
                    temp_cover_file = None

            letra = None
            try:
                letra = syncedlyrics.search(f"{song_dict['artist']} - {song_dict['name']}")
            except:
                pass

            if formato != 'wav':
                comando = [ffmpeg_exe, '-y', '-i', downloaded_file]
                
                if temp_cover_file and os.path.exists(temp_cover_file):
                    comando.extend(['-i', temp_cover_file])
                
                if formato == 'mp3':
                    comando.extend(['-map', '0:a'])
                    if temp_cover_file:
                        comando.extend(['-map', '1:v', '-c:v', 'copy', '-id3v2_version', '3'])
                        comando.extend(['-metadata:s:v', 'title="Album cover"', '-metadata:s:v', 'comment="Cover (front)"'])
                    comando.extend(['-metadata', f'title={song_dict["name"]}'])
                    comando.extend(['-metadata', f'artist={song_dict["artist"]}'])
                    comando.extend(['-metadata', f'album={song_dict["album"]}'])
                    comando.extend(['-metadata', f'date={song_dict["year"]}'])
                    comando.extend(['-codec:a', 'copy', temp_output])

                elif formato == 'm4a':
                    comando.extend(['-map', '0:a'])
                    if temp_cover_file:
                        comando.extend(['-map', '1:v', '-c:v', 'copy', '-disposition:v', 'attached_pic'])
                    comando.extend(['-metadata', f'title={song_dict["name"]}'])
                    comando.extend(['-metadata', f'artist={song_dict["artist"]}'])
                    comando.extend(['-metadata', f'album={song_dict["album"]}'])
                    comando.extend(['-metadata', f'date={song_dict["year"]}'])
                    comando.extend(['-codec:a', 'copy', temp_output])

                elif formato == 'flac':
                    comando.extend(['-map', '0:a'])
                    if temp_cover_file:
                        comando.extend(['-map', '1:v', '-c:v', 'png', '-disposition:v', 'attached_pic'])
                    comando.extend(['-metadata', f'title={song_dict["name"]}'])
                    comando.extend(['-metadata', f'artist={song_dict["artist"]}'])
                    comando.extend(['-metadata', f'album={song_dict["album"]}'])
                    comando.extend(['-metadata', f'date={song_dict["year"]}'])
                    comando.extend(['-codec:a', 'copy', temp_output])
                
                subprocess.run(comando, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                os.remove(downloaded_file)
                os.replace(temp_output, output_path)
            else:
                os.replace(downloaded_file, output_path)
            
            if letra and formato != 'wav':
                try:
                    if formato == 'mp3':
                        from mutagen.mp3 import MP3
                        audio = MP3(output_path, ID3=ID3)
                        if audio.tags is None: audio.add_tags()
                        audio.tags.add(USLT(encoding=3, lang='eng', desc='', text=letra))
                        audio.save(v2_version=3)
                    elif formato == 'm4a':
                        from mutagen.mp4 import MP4
                        audio = MP4(output_path)
                        audio['©lyr'] = [letra]
                        audio.save()
                    elif formato == 'flac':
                        from mutagen.flac import FLAC
                        audio = FLAC(output_path)
                        audio['lyrics'] = letra
                        audio.save()
                except Exception as e:
                    print(f"No se pudo incrustar la letra en {song_dict['name']}: {e}")

            if temp_cover_file and os.path.exists(temp_cover_file):
                os.remove(temp_cover_file)

            return output_path
        except Exception as e:
            try:
                with open("error_debug.txt", "a", encoding="utf-8") as f:
                    f.write(f"Error al descargar '{song_dict['name']}':\n{str(e)}\n{'-'*40}\n")
            except: pass
            print(f"Error al descargar {song_dict['name']}: {e}")
            
            if 'temp_download_path' in locals():
                if os.path.exists(f"{temp_download_path}.{formato}"): os.remove(f"{temp_download_path}.{formato}")
            return None