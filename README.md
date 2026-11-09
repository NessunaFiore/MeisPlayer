# Mei's Player

![Estado](https://img.shields.io/badge/Estado-Beta-blue)
![Python](https://img.shields.io/badge/Python-3.10+-yellow)
![Licencia](https://img.shields.io/badge/Licencia-MIT-green)

Mei's Player es una aplicación de escritorio Open Source diseñada para ayudar a conservar música de Spotify en formato local (MP3, M4A, FLAC y WAV) para escucharla sin conexión a internet.

Este proyecto nació de la necesidad de tener un respaldo personal de la música, ya que las plataformas a veces eliminan contenido de forma repentina. La aplicación obtiene los metadatos (título, artista, álbum, año y portada) directamente de la API de Spotify, y busca el audio en YouTube Music (con un sistema de respaldo en YouTube normal) para descargarlo con sus etiquetas y carátulas incrustadas.

## Características

* Búsqueda por URL: Pega el enlace de una playlist o canción de Spotify.
* Metadatos completos: Descarga el archivo con el título, artista, álbum, año y portada incrustados.
* Letras: Busca y añade la letra de la canción automáticamente (si está disponible).
* Sistema de respaldo: Si una canción está bloqueada o restringida en YouTube Music, el programa busca automáticamente una versión alternativa en YouTube normal.
* Reanudación: Si cierras el programa, al volver a intentar la descarga, el sistema omite las canciones que ya existen y continúa donde se quedó (debes seleccionar la misma carpeta donde ya habías iniciado tu descarga).
* Selector de carpeta: Permite elegir la ubicación exacta donde se guardará la música.
* Organización inteligente: Si dos canciones tienen el mismo nombre pero diferente artista, las guarda como "Canción - Artista" para no sobrescribir archivos.

## Descarga e Instalación

La forma más fácil de usar Mei's Player es descargar el instalador desde la sección de **[Releases](https://github.com/NessunaFiore/MeisPlayer/releases)** de este repositorio.

1. Descarga el archivo `MeisPlayer Release 1.X.exe`.
2. Ejecútalo.
3. Abre la aplicación desde tu escritorio.

### Primer inicio y configuración de API Keys
Al abrir la aplicación por primera vez, verás una ventana de bienvenida. 
1. Haz clic en **"Ver Tutorial"** para aprender cómo obtener tus propias llaves de Spotify en el Developer Dashboard (el tutorial incluye un enlace directo).
2. Pega tu **Client ID** y **Client Secret** en los recuadros.
3. Haz clic en **"Guardar y Abrir App"**. La aplicación recordará tus llaves en un archivo `config.json` local para futuros usos.

## Para Desarrolladores (Código Fuente)

Si deseas modificar el código o compilar tu propia versión, puedes descargar el archivo `MeisPlayer-Source.zip` desde la sección de **Releases**. Este archivo contiene el código Python y el FFmpeg necesario.

1. Extrae el archivo `.zip` en una carpeta.
2. Asegúrate de tener Python instalado.
3. Abre una terminal en la carpeta y ejecuta:
Asegúrate de tener Python instalado. Abre una terminal en la carpeta del proyecto y ejecuta:
```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```
4. Ejecutar o Compilar la aplicación

EJECUTAR:
```bash 
python Main.py
```
COMPILAR:
```bash 
pyinstaller --noconfirm --onedir --windowed --name "MeisPlayer" --icon="Mei.ico" --add-data "Mei.ico;." --add-data "ffmpeg.exe;." --add-data "ffprobe.exe;." --add-data "tutorial_1.jpg;." --add-data "tutorial_2.jpg;." --add-data "tutorial_3.jpg;." --collect-all ytmusicapi Main.py
```

## Limitaciones conocidas (Modo de Desarrollo de Spotify)

Debido a las políticas actuales de Spotify para aplicaciones en modo de desarrollo:
1. Límite de usuarios: La aplicación solo puede ser usada por un máximo de 5 usuarios. Si deseas invitar a alguien, el dueño de la API debe agregar su correo en el panel de control de desarrolladores de Spotify.
2. Playlists de terceros: La API de Spotify no permite leer playlists creadas por otros usuarios. Solo se pueden descargar playlists creadas o guardadas en la biblioteca propia.
3. Cuenta Premium: El dueño de las API keys debe tener una cuenta de Spotify Premium activa. Los usuarios agregados al proyecto (paso 1) no lo necesitan.

## Descargo de Responsabilidad

Mei's Player es una herramienta creada con fines educativos y para uso personal (conservación de música para escuchar offline sin depender de subcriones o servicios de streming).
* El desarrollador de esta aplicación no se hace responsable del uso que los usuarios le den al software.
* Este proyecto no está afiliado ni respaldado por Spotify o YouTube.
* Al usar esta herramienta, el usuario asume toda la responsabilidad de cumplir con los Términos de Servicio de las plataformas mencionadas.

## Créditos

Este es un proyecto personal en estado Beta, creado y motivado por la conservacion de las biblioteca digitales. Si encuentras un error o tienes una idea para mejorarlo, eres bienvenido a abrir un Issue o enviar un Pull Request.

## Agradecimientos

Este proyecto no hubiese sido posible sin la ayuda de Chris, aquella persona que me motivo e inspiro para la creacion de este proyecto
