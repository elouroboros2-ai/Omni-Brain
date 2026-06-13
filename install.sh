#!/bin/bash

echo "🧠 Iniciando la instalación de Omni-Brain..."

# 1. Comprobar si Homebrew está instalado (solo para macOS por ahora)
if ! command -v brew &> /dev/null
then
    echo "🍺 Homebrew no está instalado. Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 2. Instalar dependencias del sistema operativo
echo "📦 Instalando dependencias del sistema (ffmpeg, yt-dlp, portaudio)..."
brew install ffmpeg yt-dlp portaudio

# 3. Instalar Ollama si no está presente
if ! command -v ollama &> /dev/null
then
    echo "🦙 Instalando Ollama..."
    brew install --cask ollama
    echo "⚠️ Por favor, abre la aplicación Ollama desde tu carpeta de Aplicaciones para iniciar el servidor de fondo."
fi

# 4. Descargar el modelo qwen2.5:7b
echo "🧠 Descargando el modelo de Inteligencia Artificial (qwen2.5:7b)..."
echo "⏳ Esto puede tardar varios minutos dependiendo de tu conexión a internet..."
ollama pull qwen2.5:7b

# 5. Crear el entorno virtual y Python
echo "🐍 Configurando el entorno de Python..."
python3 -m venv jarvis_env
source jarvis_env/bin/activate

# 6. Instalar librerías de Python
echo "📚 Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

# 7. Crear el script de inicio rápido
echo "🚀 Creando el comando de inicio rápido (start.command)..."
cat << 'EOF' > start.command
#!/bin/bash
cd "$(dirname "$0")"
source jarvis_env/bin/activate
python3 main.py
EOF
chmod +x start.command

echo "✅ ¡Instalación Completada con Éxito!"
echo "Para iniciar Omni-Brain, simplemente haz doble clic en el archivo 'start.command' o ejecuta './start.command' en tu terminal."
