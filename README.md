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
* Seguimiento de descargas: La lista centra automáticamente la canción activa y coloca los errores al principio al terminar el lote.
* Tema oscuro permanente en la ventana principal, configuración y tutorial.

## Descargo de Responsabilidad

Mei's Player es una herramienta creada con fines educativos y para uso personal (conservación de música para escuchar offline).
* El desarrollador de esta aplicación no se hace responsable del uso que los usuarios le den al software.
* Este proyecto no está afiliado ni respaldado por Spotify o YouTube.
* Al usar esta herramienta, el usuario asume toda la responsabilidad de cumplir con los Términos de Servicio de las plataformas mencionadas.

## Limitaciones conocidas (Modo de Desarrollo de Spotify)

Debido a las políticas actuales de Spotify para aplicaciones en modo de desarrollo:
1. Límite de usuarios: La aplicación solo puede ser usada por un máximo de 5 usuarios. Si deseas invitar a alguien, el dueño de la API debe agregar su correo en el panel de control de desarrolladores de Spotify.
2. Playlists de terceros: La API de Spotify no permite leer playlists creadas por otros usuarios. Solo se pueden descargar playlists creadas o guardadas en la biblioteca propia.
3. Cuenta Premium: El dueño de las API keys debe tener una cuenta de Spotify Premium activa. Los usuarios agregados al proyecto (paso 1) no lo necesitan.

## Instalación desde código fuente

Para usar esta aplicación, es necesario descargar el código fuente desde la sección de [Releases](https://github.com/TU_USUARIO/MeisPlayer/releases) y compilarla tú mismo. Esto se debe a que el repositorio no incluye las claves de la API de Spotify ni un ejecutable precompilado.

Sigue estos pasos para compilarlo:

### 1. Descargar y extraer el proyecto
Descarga el archivo `.zip` desde la sección de **Releases** y extráelo en una carpeta de tu preferencia.

### 2. Instalar Python y las dependencias
Asegúrate de tener Python instalado. Abre una terminal en la carpeta del proyecto y ejecuta:
```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt

### Limitaciones conocidas (Modo de Desarrollo de Spotify)

Debido a las políticas actuales de Spotify para aplicaciones en modo de desarrollo:
1. Límite de usuarios: La aplicación solo puede ser usada por un máximo de 5 usuarios. Si deseas invitar a alguien, el dueño de la API debe agregar su correo en el panel de control de desarrolladores de Spotify.
2. Playlists de terceros: La API de Spotify no permite leer playlists creadas por otros usuarios. Solo se pueden descargar playlists creadas o guardadas en la biblioteca propia.
3. Cuenta Premium: El dueño de las Api keys debe tener una cuenta de Spotify Premium activa. Los usuarios agregados al proyecto (paso 1) no lo necesitan.