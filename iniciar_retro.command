#!/bin/bash
cd "$(dirname "$0")"

echo "Arrancando OmniPlayer Retro..."
# Usamos el entorno virtual de Omni-Brain
./jarvis_env/bin/python retro_gui.py
