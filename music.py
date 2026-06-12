import os
import subprocess
import threading
import tempfile
import queue
import time

class MusicPlayer:
    def __init__(self):
        self.current_process = None
        self.audio_file = None
        self.playlist_queue = queue.Queue()
        self.is_playing = False
        self.is_paused = False
        self.worker_thread = None
        self.current_song_title = None
        self.history = []
        self.library_dir = os.path.join(os.path.dirname(__file__), "OmniLibrary")
        os.makedirs(self.library_dir, exist_ok=True)

    def get_current_song(self):
        return self.current_song_title

    def play(self, query, count=1):
        self.stop()
        self.is_playing = True
        threading.Thread(target=self._start_playlist, args=(query, count), daemon=True).start()

    def _start_playlist(self, query, count):
        print(f"[Music] Buscando {count} pistas para: {query} (puede tardar 5-10 segundos)...")
        try:
            cmd = ["yt-dlp", f"ytsearch{count}:{query}", "--print", "%(id)s|%(title)s", "--no-warnings"]
            
            # Mecanismo de reintentos para evitar errores aleatorios de yt-dlp
            result = None
            for attempt in range(3):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    break
                except subprocess.CalledProcessError:
                    if attempt == 2:
                        raise
                    time.sleep(1)
            
            lines = result.stdout.strip().split('\n')
            
            for line in lines:
                if line and '|' in line:
                    video_id, title = line.split('|', 1)
                    self.playlist_queue.put((video_id, title))
            
            if self.playlist_queue.empty():
                print(f"[Music Error] No se encontraron resultados para: {query}")
                self.is_playing = False
                import tts
                tts.speak("No pude encontrar canciones para esa búsqueda.")
                return
                    
            if self.worker_thread is None or not self.worker_thread.is_alive():
                self.worker_thread = threading.Thread(target=self._playlist_worker, daemon=True)
                self.worker_thread.start()
        except Exception as e:
            print(f"[Music Error] Falló la búsqueda de playlist: {e}")
            self.is_playing = False
            import tts
            tts.speak("Ocurrió un error al intentar buscar la música en YouTube.")

    def _add_to_playlist(self, query):
        print(f"[Music Radio] Buscando: {query}...")
        try:
            cmd = ["yt-dlp", f"ytsearch1:{query}", "--print", "%(id)s|%(title)s", "--no-warnings"]
            result = None
            for attempt in range(3):
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    break
                except subprocess.CalledProcessError:
                    if attempt == 2: raise
                    time.sleep(1)
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line and '|' in line:
                    v_id, t = line.split('|', 1)
                    self.playlist_queue.put((v_id, t))
        except Exception as e:
            print(f"[Music Radio Error] {e}")

    def _playlist_worker(self):
        while self.is_playing:
            try:
                item = self.playlist_queue.get(timeout=1)
                video_id, title = item
            except queue.Empty:
                if self.current_process and self.current_process.poll() is None:
                    continue
                # Si la cola está vacía pero is_playing sigue True, Radio Infinita
                if self.is_playing:
                    print("[Music Radio] Calculando siguiente pista...")
                    import llm
                    history_titles = [t for _, t in self.history[-3:]]
                    next_query = llm.generate_radio_next(history_titles)
                    self._add_to_playlist(next_query)
                    # Comprobar de nuevo si añadió algo, sino salir para evitar loops infinitos fallidos
                    if self.playlist_queue.empty():
                        break
                    continue
                break
                
            import re
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
            temp_path = os.path.join(self.library_dir, f"{video_id}_{safe_title}.m4a")
            
            try:
                if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                    print(f"[Music] Pre-descargando ID {video_id} en OmniLibrary...")
                    subprocess.run([
                        "yt-dlp", "-x", "--audio-format", "m4a", "--force-overwrites", video_id, "-o", temp_path
                    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    print(f"[Music] Pista '{title}' encontrada en Caché Local. (Cero uso de red)")
                
                # Esperar a que la canción anterior termine
                while self.current_process and self.current_process.poll() is None and self.is_playing:
                    time.sleep(0.2)
                    
                if not self.is_playing:
                    break
                    
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    self._cleanup() # Limpiar estado anterior
                    self.audio_file = temp_path
                    self.current_song_title = title
                    self.history.append((video_id, title))
                    if len(self.history) > 10:
                        self.history.pop(0)
                        
                    print(f"[Music] Reproduciendo audio en fondo: {title}...")
                    self.current_process = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", temp_path])
                    self.current_process.wait()  # Esperar a que termine de sonar
                else:
                    print(f"[Music Error] Falló la descarga de {video_id}")
                    
            except Exception as e:
                print(f"[Music Error Worker] {e}")
        
        # Cuando el trabajador termina (lista vacía o detenido)
        self.is_playing = False
        self.current_song_title = None
        self.current_process = None

    def next(self):
        print("[Music] Saltando a la siguiente pista...")
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.kill()
            except: pass
        os.system("killall ffplay 2>/dev/null")

    def stop(self):
        print("[Music] Deteniendo reproducción y limpiando cola.")
        self.is_playing = False
        while not self.playlist_queue.empty():
            try: self.playlist_queue.get_nowait()
            except queue.Empty: break
            
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.kill()
            except: pass
            self.current_process = None
            
        os.system("killall ffplay 2>/dev/null")
        self._cleanup()

    def pause(self):
        import signal
        if self.current_process:
            self.is_paused = True
            try: self.current_process.send_signal(signal.SIGSTOP)
            except: pass

    def resume(self):
        import signal
        if self.current_process:
            self.is_paused = False
            try: self.current_process.send_signal(signal.SIGCONT)
            except: pass

    def _cleanup(self):
        self.current_song_title = None
        self.audio_file = None
