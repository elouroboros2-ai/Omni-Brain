import pyaudio
import wave
import numpy as np
import os
from faster_whisper import WhisperModel
import tempfile

class EarEngine:
    def __init__(self):
        print("[EarEngine] Cargando modelo Whisper (base)...")
        # Cambiamos a 'base' para mucha mejor precisión en español/francés
        self.model = WhisperModel("base", device="cpu", compute_type="int8")
        
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        
        self.SILENCE_THRESHOLD = 500
        self.SILENCE_DURATION = 1.0 # Reducido a 1.0 para que sienta que responde más rápido
        
    def listen_until_silence(self):
        """Graba audio hasta detectar silencio continuo y devuelve el archivo temporal."""
        self.stream = self.p.open(format=self.FORMAT,
                                  channels=self.CHANNELS,
                                  rate=self.RATE,
                                  input=True,
                                  frames_per_buffer=self.CHUNK)
        
        print("[EarEngine] Escuchando...")
        frames = []
        silent_chunks = 0
        max_silent_chunks = int(self.RATE / self.CHUNK * self.SILENCE_DURATION)
        
        # Ignorar primer medio segundo de ruido de inicialización del micro
        for _ in range(int(self.RATE / self.CHUNK * 0.5)):
            self.stream.read(self.CHUNK, exception_on_overflow=False)
            
        self.is_recording = True
        
        while self.is_recording:
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)
                
                # Detección de silencio RMS
                audio_np = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(np.square(audio_np.astype(np.float32))))
                
                if rms < self.SILENCE_THRESHOLD:
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                    
                if silent_chunks > max_silent_chunks:
                    break
            except Exception as e:
                print(f"[Audio Error] {e}")
                break
                
        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()
        
        if len(frames) > max_silent_chunks:
            fd, temp_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            
            wf = wave.open(temp_path, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            return temp_path
        return None

    def transcribe(self, audio_path, forced_language=None):
        """Convierte el audio a texto usando Faster Whisper."""
        if not audio_path:
            return "", "es"
            
        print("[EarEngine] Transcribiendo y detectando idioma...")
        # Activamos VAD filter para IGNORAR silencios y evitar alucinaciones
        segments, info = self.model.transcribe(
            audio_path, 
            beam_size=5, 
            language=forced_language,
            vad_filter=True, 
            vad_parameters=dict(min_silence_duration_ms=500),
            condition_on_previous_text=False
        )
        texto = "".join([segment.text for segment in segments]).strip()
        
        try:
            os.remove(audio_path)
        except: pass
        
        return texto, info.language

if __name__ == "__main__":
    ear = EarEngine()
    print("Habla ahora...")
    audio_file = ear.listen_until_silence()
    print(f"Detectado: {text}")
