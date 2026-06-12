import rumps
import threading
from pynput import keyboard
import time
import numpy as np
from openwakeword.model import Model

from stt import EarEngine
from tts import speak
from llm import generate_response
from music import MusicPlayer

class JarvisApp(rumps.App):
    def __init__(self):
        super(JarvisApp, self).__init__("🧠", quit_button=None)
        
        self.ear = EarEngine()
        self.music = MusicPlayer()
        self.is_processing = False
        self.scroll_index = 0
        
        # --- UI MENU ---
        self.status_item = rumps.MenuItem("🟢 Estado: Listo")
        
        # Reproductor Submenu
        self.reproductor_menu = rumps.MenuItem("🎵 Reproductor")
        self.play_pause_item = rumps.MenuItem("⏯️ Pausar / Reanudar", callback=self.toggle_music)
        self.next_item = rumps.MenuItem("⏭️ Siguiente Canción", callback=self.next_music)
        self.stop_item = rumps.MenuItem("⏹️ Detener Música", callback=self.stop_music)
        self.reproductor_menu.add(self.play_pause_item)
        self.reproductor_menu.add(self.next_item)
        self.reproductor_menu.add(self.stop_item)
        
        # Idiomas
        self.lang_auto = rumps.MenuItem("🤖 Automático", callback=self.set_lang_auto)
        self.lang_es = rumps.MenuItem("🇪🇸 Español", callback=self.set_lang_es)
        self.lang_fr = rumps.MenuItem("🇫🇷 Francés", callback=self.set_lang_fr)
        self.lang_en = rumps.MenuItem("🇺🇸 Inglés", callback=self.set_lang_en)
        self.lang_auto.state = 1
        
        self.lang_menu = rumps.MenuItem("🗣️ Idioma de Escucha")
        self.lang_menu.add(self.lang_auto)
        self.lang_menu.add(self.lang_es)
        self.lang_menu.add(self.lang_fr)
        self.lang_menu.add(self.lang_en)
        
        self.forced_lang = None
        
        # Voz
        self.tts_edge = rumps.MenuItem("🌐 Voz Premium (Internet)", callback=self.set_tts_edge)
        self.tts_mac = rumps.MenuItem("⚡ Voz Rápida (Offline)", callback=self.set_tts_mac)
        self.tts_edge.state = 1
        
        self.voz_menu = rumps.MenuItem("🔊 Motor de Voz")
        self.voz_menu.add(self.tts_edge)
        self.voz_menu.add(self.tts_mac)
        
        # Configuración Submenu
        self.config_menu = rumps.MenuItem("⚙️ Configuración")
        self.config_menu.add(self.lang_menu)
        self.config_menu.add(self.voz_menu)
        
        self.menu = [
            self.status_item,
            None,
            self.reproductor_menu,
            None,
            self.config_menu,
            None,
            rumps.MenuItem("🔴 Salir", callback=rumps.quit_application)
        ]
        # Cargar Wake Word Model de OpenWakeWord
        # Asegurarnos de descargar los modelos onnx primero si no existen
        from openwakeword.utils import download_models
        try:
            download_models()
        except: pass
        
        print("[Jarvis] Cargando modelo Wake Word...")
        self.oww_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
        
        # Hilos
        threading.Thread(target=self.hotkey_listener, daemon=True).start()
        threading.Thread(target=self.wakeword_listener, daemon=True).start()
        threading.Thread(target=self.terminal_listener, daemon=True).start()
        
        print("[Jarvis] Listo. Presiona Ctrl+Espacio, di 'Hey Jarvis', o escribe en la consola.")

    def hotkey_listener(self):
        # Escucha el atajo Control + Espacio en todo el sistema
        with keyboard.GlobalHotKeys({'<ctrl>+<space>': self.on_trigger}) as h:
            h.join()
            
    def terminal_listener(self):
        import sys
        time.sleep(2)
        print("\n--- Modo Consola Activado ---")
        print("Puedes escribir tus comandos aquí y presionar Enter (no verás el cursor de Jarvis para evitar bloqueos visuales):")
        while True:
            try:
                text = sys.stdin.readline()
                if not text:
                    break
                text = text.strip()
                if text:
                    if self.is_processing:
                        print("[Jarvis] Estoy ocupado procesando, espera...")
                        continue
                    self.is_processing = True
                    self.title = "💬"
                    self.status_item.title = "Estado: Procesando comando..."
                    self.music.pause()
                    # Se asume idioma español en texto si no hay forma de detectarlo fácil
                    threading.Thread(target=self.execute_text_command, args=(text, "es"), daemon=True).start()
            except (KeyboardInterrupt, EOFError):
                break
            
    def wakeword_listener(self):
        CHUNK = 1280
        # Iniciar stream pasivo
        stream = self.ear.p.open(format=self.ear.FORMAT, channels=1, rate=16000, input=True, frames_per_buffer=CHUNK)
        
        while True:
            if self.is_processing:
                # Si Jarvis está escuchando la pregunta o hablando, pausamos el wakeword
                time.sleep(0.5)
                # Purgar el buffer del micro
                try:
                    stream.read(stream.get_read_available(), exception_on_overflow=False)
                except: pass
                continue
                
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_np = np.frombuffer(data, dtype=np.int16)
                
                prediction = self.oww_model.predict(audio_np)
                
                score = list(prediction.values())[0] if prediction else 0.0
                
                if score > 0.6:
                    print("\n[Wake Word] ¡Detectado 'Hey Jarvis'!")
                    self.on_trigger()
                    self.oww_model.reset()
                    time.sleep(1) # Cooldown
            except Exception as e:
                print(f"[Wake Word Error] {e}")
                time.sleep(1)

    def on_trigger(self):
        if self.is_processing:
            return
            
        # Reproducir un sonido de notificación nativo de Mac
        import os
        os.system("ffplay -nodisp -autoexit -loglevel quiet /System/Library/Sounds/Tink.aiff >/dev/null 2>&1 &")
        
        self.is_processing = True
        self.title = "🎙️"
        self.status_item.title = "Estado: Escuchando..."
        
        threading.Thread(target=self.process_interaction, daemon=True).start()
        
    def process_interaction(self):
        # Pausar la música mientras escuchamos y procesamos
        self.music.pause()
        try:
            # 1. Grabar audio con VAD
            audio_file = self.ear.listen_until_silence()
            
            # 2. Transcribir con Faster Whisper y detectar idioma
            text, lang = self.ear.transcribe(audio_file, forced_language=self.forced_lang)
            if self.forced_lang:
                lang = self.forced_lang
            print(f"\nUsuario ({lang}): {text}")
            
            if not text:
                self.music.resume()
                self.reset_state()
                return
                
            self.execute_text_command(text, lang)
            
        except Exception as e:
            print(f"Error procesando audio: {e}")
            self.music.resume()
            self.reset_state()
            
    def execute_text_command(self, text, lang="es"):
        try:
            text_lower = text.lower()
            
            # Mapeo de voces TTS según el idioma detectado
            voice_id = "es-MX-JorgeNeural"
            if lang == "fr":
                voice_id = "fr-FR-HenriNeural"
            elif lang == "en":
                voice_id = "en-US-ChristopherNeural"
            elif lang == "it":
                voice_id = "it-IT-DiegoNeural"
            elif lang == "de":
                voice_id = "de-DE-ConradNeural"
            
            # --- COMANDOS DEL SISTEMA LOCALES (Instantáneos) ---
            if "qué hora es" in text_lower or "que hora es" in text_lower or "dime la hora" in text_lower or "quelle heure est-il" in text_lower or "what time is it" in text_lower:
                from datetime import datetime
                ahora = datetime.now()
                hora = ahora.strftime("%I").lstrip("0")
                min_str = "en punto" if ahora.minute == 0 else f"y {ahora.minute}"
                ampm = "de la mañana" if ahora.hour < 12 else ("de la tarde" if ahora.hour < 20 else "de la noche")
                confirm_text = f"Son las {hora} {min_str} {ampm}."
                if lang == "fr": confirm_text = f"Il est {ahora.strftime('%H')} heure {ahora.minute if ahora.minute > 0 else ''}."
                elif lang == "en": confirm_text = f"It's {ahora.strftime('%I:%M %p')}."
                speak(confirm_text, voice=voice_id)
                self.music.resume()
                self.reset_state()
                return
                
            if any(w in text_lower for w in ["sube el volumen", "subir el volumen", "aumenta el volumen", "monte le volume", "augmenter le son", "volume up"]):
                import os
                os.system('osascript -e "set volume output volume (output volume of (get volume settings) + 20)"')
                speak("Listo." if lang == "es" else ("Fait." if lang == "fr" else "Done."), voice=voice_id)
                self.music.resume()
                self.reset_state()
                return
                
            if any(w in text_lower for w in ["baja el volumen", "bajar el volumen", "disminuye el volumen", "baisse le volume", "diminuer le son", "volume down"]):
                import os
                os.system('osascript -e "set volume output volume (output volume of (get volume settings) - 20)"')
                speak("Listo." if lang == "es" else ("Fait." if lang == "fr" else "Done."), voice=voice_id)
                self.music.resume()
                self.reset_state()
                return
                
            if any(w in text_lower for w in ["volumen al máximo", "todo el volumen", "volume au maximum", "volume to max"]):
                import os
                os.system('osascript -e "set volume output volume 100"')
                speak("Volumen al máximo." if lang == "es" else ("Volume au maximum." if lang == "fr" else "Max volume."), voice=voice_id)
                self.music.resume()
                self.reset_state()
                return
            # ---------------------------------------------------

            # --- NLP INTENT ROUTER ---
            from llm import process_command_with_llm, inject_system_context
            intent_data = process_command_with_llm(text)
            intent = str(intent_data.get("intent", "CHAT")).upper()
            
            if intent != "CHAT":
                inject_system_context(text, f"Se ejecutó la acción: {intent} con datos {intent_data}")
            
            if intent == "PLAY_MUSIC":
                query = intent_data.get("query", "")
                is_playlist = intent_data.get("is_playlist", False)
                if isinstance(is_playlist, str):
                    is_playlist = is_playlist.lower() == "true"
                count = 10 if is_playlist else 1
                
                if query:
                    if is_playlist:
                        confirm_text = f"Armando playlist de {query}."
                        if lang == "fr": confirm_text = f"Préparation de la playlist pour {query}."
                        elif lang == "en": confirm_text = f"Starting playlist for {query}."
                    else:
                        confirm_text = f"Claro, enseguida pongo {query}."
                        if lang == "fr": confirm_text = f"Bien sûr, je mets {query}."
                        elif lang == "en": confirm_text = f"Sure, playing {query}."
                    
                    print(f"\nJarvis: {confirm_text}")
                    speak(confirm_text, voice=voice_id)
                    self.music.play(query, count=count)
                    self.reset_state()
                    return
            
            elif intent == "STOP_MUSIC":
                self.music.stop()
                confirm_text = "Música detenida."
                if lang == "fr": confirm_text = "Musique arrêtée."
                elif lang == "en": confirm_text = "Music stopped."
                print(f"\nJarvis: {confirm_text}")
                speak(confirm_text, voice=voice_id)
                self.reset_state()
                return
                
            elif intent == "NEXT_MUSIC":
                self.music.next()
                self.reset_state()
                return
                
            elif intent == "CURRENT_MUSIC":
                song = self.music.get_current_song()
                if song:
                    confirm_text = f"Estamos escuchando {song}."
                    if lang == "fr": confirm_text = f"Nous écoutons {song}."
                    elif lang == "en": confirm_text = f"We are listening to {song}."
                else:
                    confirm_text = "No estoy reproduciendo nada."
                    if lang == "fr": confirm_text = "Je ne joue rien en ce moment."
                    elif lang == "en": confirm_text = "I am not playing anything right now."
                print(f"\nJarvis: {confirm_text}")
                speak(confirm_text, voice=voice_id)
                self.music.resume()
                self.reset_state()
                return
            
            elif intent == "WEATHER":
                import requests
                try:
                    res = requests.get('https://wttr.in/?format=3', timeout=3)
                    clima = res.text.strip()
                    prompt = f"El usuario preguntó por el clima. Los datos actuales devueltos por el sistema son: {clima}. Responde brevemente y de forma hablada muy natural, sin asteriscos ni markdown."
                    response = generate_response(prompt, detected_lang=lang)
                    speak(response, voice=voice_id)
                except Exception as e:
                    speak("Lo siento, no pude obtener el clima." if lang=="es" else "Sorry, I couldn't get the weather.", voice=voice_id)
                self.music.resume()
                self.reset_state()
                return
                
            elif intent == "BATTERY":
                import subprocess
                try:
                    out = subprocess.check_output(["pmset", "-g", "batt"]).decode("utf-8")
                    prompt = f"El usuario preguntó por la batería. Los datos del sistema son:\n{out}\nResponde de forma hablada natural, mencionando el porcentaje actual y sin usar markdown."
                    response = generate_response(prompt, detected_lang=lang)
                    speak(response, voice=voice_id)
                except Exception:
                    speak("No pude leer la batería." if lang=="es" else "Couldn't read the battery.", voice=voice_id)
                self.music.resume()
                self.reset_state()
                return
                
            elif intent == "OPEN_APP":
                query = intent_data.get("query", "")
                if query:
                    import os
                    os.system(f'open -a "{query}"')
                    confirm = f"Abriendo {query}." if lang=="es" else f"Opening {query}."
                    if lang == "fr": confirm = f"J'ouvre {query}."
                    speak(confirm, voice=voice_id)
                self.music.resume()
                self.reset_state()
                return
            
            elif intent == "TIMER":
                seconds = intent_data.get("duration_seconds", 60)
                reason = intent_data.get("reason", "alarma")
                
                def timer_done():
                    self.music.pause()
                    import time
                    time.sleep(1)
                    speak(f"Aviso importante: {reason}." if lang=="es" else f"Important reminder: {reason}.", voice=voice_id)
                    time.sleep(3)
                    self.music.resume()
                    
                import threading
                threading.Timer(seconds, timer_done).start()
                
                confirm_text = f"Temporizador de {seconds} segundos para {reason}."
                if lang == "fr": confirm_text = f"Minuteur de {seconds} secondes."
                elif lang == "en": confirm_text = f"Timer set for {seconds} seconds."
                speak(confirm_text, voice=voice_id)
                self.music.resume()
                self.reset_state()
                return

            elif intent == "CUSTOM_SCRIPT":
                query = intent_data.get("query", "").lower()
                import os
                scripts_dir = "comandos_personalizados"
                if not os.path.exists(scripts_dir):
                    os.makedirs(scripts_dir)
                    
                script_found = False
                for script in os.listdir(scripts_dir):
                    if script.endswith(".sh") or script.endswith(".command"):
                        name = script.replace(".sh", "").replace(".command", "").lower()
                        if any(word in query for word in name.split("_")) or name in query:
                            script_path = os.path.join(scripts_dir, script)
                            os.system(f"sh '{script_path}' &")
                            script_found = True
                            speak("Comando ejecutado." if lang=="es" else "Command executed.", voice=voice_id)
                            break
                            
                if not script_found:
                    speak("No encontré un script para eso." if lang=="es" else "No script found for that.", voice=voice_id)
                self.music.resume()
                self.reset_state()
                return

            

                
            # 3. Enviar a LLM
            self.title = "💬"
            # Para latencia ultra-baja en voz, podríamos interceptar las primeras frases.
            # Aquí usamos TTS completo por simplicidad.
            response = generate_response(text, detected_lang=lang)
            
            print(f"\nJarvis: {response}\n")
            
            # 4. Hablar
            self.title = "🔊"
            speak(response, voice=voice_id)
            
            # Reanudar música si estaba sonando
            self.music.resume()
            
        except Exception as e:
            print(f"Error procesando: {e}")
            self.music.resume()
        finally:
            self.reset_state()
            
    def reset_state(self):
        self.title = "🧠"
        self.status_item.title = "Estado: Esperando"
        self.is_processing = False

    # --- CALLBACKS DEL MENÚ ---
    def toggle_music(self, _):
        if self.music.is_paused:
            self.music.resume()
        else:
            self.music.pause()

    def next_music(self, _):
        self.music.next()

    def stop_music(self, _):
        self.music.stop()

    def _clear_lang_states(self):
        self.lang_auto.state = 0
        self.lang_es.state = 0
        self.lang_fr.state = 0
        self.lang_en.state = 0

    def set_lang_auto(self, _):
        self._clear_lang_states()
        self.lang_auto.state = 1
        self.forced_lang = None

    def set_lang_es(self, _):
        self._clear_lang_states()
        self.lang_es.state = 1
        self.forced_lang = "es"

    def set_lang_fr(self, _):
        self._clear_lang_states()
        self.lang_fr.state = 1
        self.forced_lang = "fr"

    def set_lang_en(self, _):
        self._clear_lang_states()
        self.lang_en.state = 1
        self.forced_lang = "en"

    def set_tts_edge(self, _):
        self.tts_edge.state = 1
        self.tts_mac.state = 0
        import tts
        tts.USE_MAC_NATIVE_TTS = False

    def set_tts_mac(self, _):
        self.tts_edge.state = 0
        self.tts_mac.state = 1
        import tts
        tts.USE_MAC_NATIVE_TTS = True

    @rumps.timer(1)
    def update_ui_loop(self, _):
        try:
            if self.is_processing:
                self.status_item.title = "⏳ Estado: Procesando..."
                if self.title != "🔊": self.title = "🧠 ⏳"
            elif self.music.is_playing and self.music.current_song_title:
                title = self.music.current_song_title
                self.status_item.title = f"🎶 Sonando: {title}"
                
                if len(title) > 25:
                    display_text = title[:22] + "..."
                else:
                    display_text = title
                    
                self.title = f"🎶 {display_text}"
            else:
                self.status_item.title = "🟢 Estado: Listo"
                self.title = "🧠"
        except Exception: pass

if __name__ == "__main__":
    app = JarvisApp()
    app.run()
