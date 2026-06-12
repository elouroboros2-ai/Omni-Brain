import os
import subprocess
import re
import tempfile

def clean_text(text):
    """Limpia el texto de caracteres especiales."""
    text = re.sub(r'[*#_~`]', '', text)
    return text.strip()

USE_MAC_NATIVE_TTS = False

def speak(text, voice="es-ES-AlvaroNeural"):
    """
    Reproduce texto a voz usando Microsoft Edge TTS o Mac Native.
    """
    if not text:
        return
        
    if USE_MAC_NATIVE_TTS:
        import subprocess
        voice_mac = "Monica"
        if "fr-" in voice: voice_mac = "Thomas"
        elif "en-" in voice: voice_mac = "Samantha"
        elif "de-" in voice: voice_mac = "Anna"
        elif "it-" in voice: voice_mac = "Alice"
        
        # -r 160 baja la velocidad para que suene más natural y menos robótica
        subprocess.run(["say", "-v", voice_mac, "-r", "160", text])
        return

    cleaned = clean_text(text)
    if not cleaned:
        return
        
    try:
        import subprocess
        fd, temp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        
        # Generar el audio neuronal
        subprocess.run(["edge-tts", "--voice", voice, "--text", cleaned, "--write-media", temp_path], check=True)
        
        # Reproducir el audio nativamente en Mac solo si se generó correctamente
        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", temp_path], check=True)
        else:
            print("[TTS Error] edge-tts devolvió un archivo vacío.")
        
        # Limpiar archivo temporal
        os.remove(temp_path)
    except Exception as e:
        print(f"[TTS Error] {e}")

if __name__ == "__main__":
    speak("Sistemas operativos, señor.")
