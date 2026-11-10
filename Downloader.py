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
import json
import asyncio
import xazam
import difflib
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

# --- NUEVO: Funciones para recordar la última carpeta de descargas ---
def obtener_ultima_carpeta():
    config_path = obtener_ruta_config()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("ULTIMA_CARPETA", os.path.expanduser("~"))
        except:
            pass
    return os.path.expanduser("~")

def guardar_ultima_carpeta(ruta):
    config_path = obtener_ruta_config()
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            pass
            
    config["ULTIMA_CARPETA"] = ruta
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"No se pudo guardar la última carpeta: {e}")

# --- NUEVO: Funciones para recordar el último formato ---
def obtener_ultimo_formato():
    config_path = obtener_ruta_config()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("ULTIMO_FORMATO", "mp3")
        except:
            pass
    return "mp3"

def guardar_ultimo_formato(formato):
    config_path = obtener_ruta_config()
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            pass
            
    config["ULTIMO_FORMATO"] = formato
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"No se pudo guardar el último formato: {e}")
# ------------------------------------------------------------------

class MusicDownloader:
    def __init__(self):
        config_path = obtener_ruta_config()
        
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

    def _verificar_audio(self, ruta_audio, artista_esperado, titulo_esperado):
        """Usa Shazam para verificar si el audio descargado es el correcto."""
        try:
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                directorio_ffmpeg = sys._MEIPASS
            else:
                directorio_ffmpeg = os.path.abspath(".")
            
            ffmpeg_exe = os.path.join(directorio_ffmpeg, "ffmpeg.exe" if os.name == 'nt' else "ffmpeg")
            temp_fragmento = ruta_audio + "_muestra.tmp"

            comando = [
                ffmpeg_exe, '-y', '-ss', '30', '-i', ruta_audio, '-t', '20', 
                '-acodec', 'libmp3lame', '-ar', '44100', '-ab', '128k', 
                '-f', 'mp3', temp_fragmento
            ]
            
            subprocess.run(comando, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

            if not os.path.exists(temp_fragmento):
                return False, None
                
            with open(temp_fragmento, "rb") as f:
                audio_bytes = f.read()

            async def _identificar():
                async with xazam.ShazamTransport() as transport:
                    client = xazam.ShazamClient(transport)
                    return await client.identify(audio_bytes)

            resultado = asyncio.run(_identificar())

            if os.path.exists(temp_fragmento):
                try: os.remove(temp_fragmento)
                except: pass

            if not resultado.matched:
                return False, None

            track = resultado.track
            return True, f"{track.subtitle} {track.title}"

        except Exception as e:
            print(f"Aviso: Error en la verificacion con Shazam: {e}")
            if 'temp_fragmento' in locals() and os.path.exists(temp_fragmento):
                try: os.remove(temp_fragmento)
                except: pass
            return False, None

    def search_songs(self, url):
        songs = []
        try:
            track_id = url.split("/track/")[-1].split("?")[0] if "/track/" in url else None
            playlist_id = url.split("/playlist/")[-1].split("?")[0] if "/playlist/" in url else None

            if playlist_id:
                results = self.sp.playlist_items(playlist_id)
                tracks = results['items']
                
                while results['next']:
                    time.sleep(1.5) 
                    results = self.sp.next(results)
                    tracks.extend(results['items'])

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
        self.last_error = None
        try:
            safe_title = "".join([c for c in song_dict['name'] if c.isalpha() or c.isdigit() or c in ' -_,']).rstrip()
            
            filename = f"{safe_title}.{formato}"
            output_path = os.path.join(carpeta_destino, filename)
            
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

                    if song_dict['artist'].lower() in artista_existente.lower():
                        return output_path
                    else:
                        safe_artist = "".join([c for c in song_dict['artist'] if c.isalpha() or c.isdigit() or c in ' -_,']).rstrip()
                        filename = f"{safe_title} - {safe_artist}.{formato}"
                        output_path = os.path.join(carpeta_destino, filename)
                        
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                            return output_path
                            
                        print(f"Artista diferente. Guardando como: {filename}")
                except Exception as e:
                    print(f"No se pudo leer los metadatos del archivo existente: {e}. Se procederá a descargar.")

            temp_download_path = os.path.join(carpeta_destino, f"tmp_{safe_title}")
            temp_output = os.path.join(carpeta_destino, f"final_{safe_title}.{formato}")
            temp_cover = os.path.join(carpeta_destino, f"tmp_cover_{safe_title}.jpg")
            
            for f in [f"{temp_download_path}.{formato}", temp_output, temp_cover]:
                if os.path.exists(f):
                    try: os.remove(f)
                    except: pass

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

            descarga_correcta = False
            nombre_para_rescate = None

            # --- 1ER INTENTO: BUSQUEDA EN YOUTUBE MUSIC (CON VERIFICACIÓN INTELIGENTE) ---
            try:
                search_results = self.ytmusic.search(query, filter="songs", limit=5)
                if search_results:
                    video_id = None
                    video_title = ""
                    duracion_spotify = song_dict.get('duration_ms', 0) / 1000
                    
                    for result in search_results:
                        if 'duration_seconds' not in result: continue
                        if abs(result['duration_seconds'] - duracion_spotify) < 10:
                            video_id = result['videoId']
                            video_title = result.get('title', '')
                            break
                    
                    if not video_id:
                        video_id = search_results[0]['videoId']
                        video_title = search_results[0].get('title', '')

                    url_youtube = f"https://www.youtube.com/watch?v={video_id}"

                    similitud = difflib.SequenceMatcher(None, song_dict['name'].lower(), video_title.lower()).ratio()
                    
                    if similitud >= 0.80:
                        print(f"Coincidencia de metadatos alta ({similitud*100:.1f}%). Saltando verificacion de Shazam.")
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url_youtube])
                        descarga_correcta = True
                    else:
                        print(f"Coincidencia de metadatos baja ({similitud*100:.1f}%). Verificando con Shazam...")
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url_youtube])
                        
                        downloaded_file = f"{temp_download_path}.{formato}"
                        if os.path.exists(downloaded_file):
                            shazam_ok, shazam_query = self._verificar_audio(downloaded_file, song_dict['artist'], song_dict['name'])
                            
                            if shazam_ok and shazam_query:
                                shazam_query_lower = shazam_query.lower()
                                titulo_spotify = song_dict['name'].lower()
                                sim_titulo = difflib.SequenceMatcher(None, titulo_spotify, shazam_query_lower).ratio()
                                
                                if sim_titulo >= 0.70:
                                    nombre_para_rescate = shazam_query
                                    print(f"Shazam confirmado por similitud de titulo. Preparando rescate usando: {nombre_para_rescate}")
                                else:
                                    print(f"Shazam se equivoco (dijo: '{shazam_query}' con {sim_titulo*100:.1f}% de similitud). Ignorando y usando metadatos de Spotify.")
                                    nombre_para_rescate = None
                                
                                os.remove(downloaded_file)
                            else:
                                print("Shazam no pudo identificar. Pasando al rescate normal...")
                                os.remove(downloaded_file)
            except Exception as e:
                print(f"Aviso: Fallo en YouTube Music para '{song_dict['name']}. INTENTANDO DESCARGA DE FUENTE ALTERNATIVA")

            # --- 2DO INTENTO: BUSQUEDA EN YOUTUBE NORMAL ---
            if not descarga_correcta:
                try:
                    if nombre_para_rescate:
                        query_rescate = nombre_para_rescate
                        print(f"Usando query de Shazam: {query_rescate}")
                    else:
                        clean_name = song_dict['name'].replace('-', ' ').replace('_', ' ')
                        clean_artist = song_dict['artist'].replace('-', ' ').replace('_', ' ')
                        query_rescate = f"{clean_artist} {clean_name}"
                        print(f"Usando query de Spotify: {query_rescate}")
                    
                    url_rescate = f"ytsearch1:{query_rescate}"
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url_rescate])
                    
                    descarga_correcta = True
                    print(f"Rescate exitoso para '{song_dict['name']}'. Se acepta el audio.")
                    
                except Exception as e:
                    raise Exception(f"Falló la descarga en ambas fuentes: {e}")

            if not descarga_correcta:
                raise Exception("No se pudo descargar el audio correcto.")

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
            self.last_error = str(e)
            try:
                with open("error_debug.txt", "a", encoding="utf-8") as f:
                    f.write(f"Error al descargar '{song_dict['name']}':\n{str(e)}\n{'-'*40}\n")
            except: pass
            print(f"Error al descargar {song_dict['name']}: {e}")
            
            if 'temp_download_path' in locals():
                if os.path.exists(f"{temp_download_path}.{formato}"): os.remove(f"{temp_download_path}.{formato}")
            return None