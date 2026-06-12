# 🧠 OmniBrain

Un asistente virtual impulsado por Inteligencia Artificial de código abierto (Ollama), diseñado para ser **100% privado, rápido y vivir directamente en la barra de menú de tu sistema**.

Actualmente, **OmniBrain** está optimizado y diseñado para ejecutarse de manera nativa en **macOS**, aunque su motor interno es multiplataforma y en el futuro se planea lanzar interfaces para Windows y Linux.

## ✨ Características Principales

- **Privacidad Total (Offline):** OmniBrain utiliza **Ollama** con el modelo `qwen2.5:7b` ejecutándose directamente en tu máquina. Ninguna de tus conversaciones, comandos o transcripciones de voz se envía a la nube.
- **Detección de Palabra de Activación (Wake Word):** Escucha activamente "Hey Jarvis" o tu palabra clave elegida, consumiendo muy pocos recursos, listo para atenderte al instante.
- **Reproductor de Música Integrado (Sin Anuncios):** Pídele que reproduzca cualquier canción o artista, y OmniBrain lo buscará y reproducirá usando `yt-dlp` y `ffplay`, mostrando una elegante marquesina (efecto de scroll) directamente en la barra superior de tu sistema.
- **Motor de Voz Híbrido:** Cuenta con síntesis de voz mediante Edge-TTS (voces hiperrealistas por internet) o Voz Nativa del Sistema (offline y rapidísima).

## 🚀 Instalación (1 Solo Clic)

Hemos preparado un script que se encarga de instalar todo lo necesario automáticamente (Homebrew, Ollama, modelo de IA, librerías de Python).

1. Abre tu **Terminal**.
2. Clona este repositorio o descarga el código fuente.
3. Navega hasta la carpeta descargada:
   ```bash
   cd ruta/a/OmniBrain
   ```
4. Otorga permisos de ejecución al script y córrelo:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

*(El instalador configurará tu entorno, descargará el modelo y dejará listo un acceso directo `start.command`)*.

## 🎧 ¿Cómo Usarlo?

Simplemente haz doble clic en el archivo `start.command` generado tras la instalación. Verás aparecer el ícono del cerebro (`🧠`) en la barra de menú superior de tu Mac.

Di: **"Hey Jarvis"** seguido de tu petición. 
- Puedes decirle: *"Pon algo de música de Bob Marley"* y disfrutar del reproductor integrado sin comerciales.
- Puedes preguntarle cualquier cosa, y la IA responderá mediante voz de forma inteligente.

## 🛠 Tecnologías Utilizadas

- **Ollama**: Motor de Inferencia Local.
- **Whisper**: Transcripción de Audio (Speech-to-Text).
- **OpenWakeWord**: Detección de palabra de activación.
- **Edge-TTS / Mac OS `say`**: Text-to-Speech.
- **yt-dlp / ffplay**: Motor de búsqueda e integración musical.
- **Rumps**: Integración nativa a la interfaz de macOS.

## 📝 Roadmap a Futuro

- Adaptación a interfaces multiplataforma (`pystray` o `PyQt`) para soportar Windows y Linux de manera nativa.
- Personalización avanzada del modelo y voces desde la misma interfaz.

---

¡Disfruta de tu asistente 100% privado y potente en la barra de tu menú! 🧠✨
