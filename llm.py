import requests
import json

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5:7b"

SYSTEM_PROMPT = """Eres Jarvis, el asistente personal de IA. Corres de forma nativa y ultrarrápida en una MacBook Pro M1.
Tu sistema actual tiene las siguientes especificaciones reales:
- Procesador: Apple M1 (8 núcleos)
- Memoria RAM: 8 GB unificados
- Tarjeta Gráfica: GPU integrada de Apple M1

REGLAS DE PERSONALIDAD:
1. Eres un amigo y asistente casual. Sé amigable pero directo.
2. Responde SIEMPRE de forma útil pero breve (máximo 1 o 2 oraciones).
3. NO hagas preguntas innecesarias al usuario. No intentes mantener una charla larga.
4. NUNCA uses formato Markdown, negritas, asteriscos o listas con guiones. Habla en texto plano."""

# Mantiene un historial corto en memoria RAM y persistente
MEMORY_FILE = "jarvis_memory.json"
history = [{"role": "system", "content": SYSTEM_PROMPT}]

def load_memory():
    global history
    import os
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                loaded = json.load(f)
                if loaded and loaded[0].get("role") == "system":
                    history = loaded
        except: pass

def save_memory():
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(history, f)
    except: pass

load_memory()

def inject_system_context(user_text, system_action):
    """Inyecta un comando de sistema en el historial para que Jarvis sepa qué pasó."""
    global history
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": f"[Acción interna del sistema: {system_action}]"})
    save_memory()

def generate_response(user_text, stream_callback=None, detected_lang="es"):
    """
    Envía texto a Ollama y retorna la respuesta.
    Si se provee stream_callback, se llama con cada fragmento de texto (útil para TTS en tiempo real).
    """
    global history
    
    # Inyectar la hora, fecha y el IDIOMA al prompt del sistema
    from datetime import datetime
    import locale
    try: locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except: pass
    fecha_hora = datetime.now().strftime("%A %d de %B de %Y, %I:%M %p")
    
    nombres_idiomas = {"es": "Español", "fr": "Francés", "en": "Inglés", "it": "Italiano", "de": "Alemán"}
    idioma_actual = nombres_idiomas.get(detected_lang, detected_lang)
    
    if history and history[0]["role"] == "system":
        history[0]["content"] = SYSTEM_PROMPT + f"\n\nCONTEXTO ACTUAL DEL SISTEMA:\n- Fecha y hora: {fecha_hora}\n- Idioma detectado del usuario: {idioma_actual}. DEBES RESPONDER ESTRICTAMENTE EN {idioma_actual.upper()}."
        
    history.append({"role": "user", "content": user_text})
    
    # Mantener historial corto para ahorrar memoria de contexto
    if len(history) > 11:
        history = [history[0]] + history[-10:]

    payload = {
        "model": MODEL,
        "messages": history,
        "stream": stream_callback is not None
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=stream_callback is not None, timeout=60)
        response.raise_for_status()
        
        full_response = ""
        if stream_callback:
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content", "")
                    if chunk:
                        full_response += chunk
                        stream_callback(chunk)
        else:
            data = response.json()
            full_response = data.get("message", {}).get("content", "")
            
        history.append({"role": "assistant", "content": full_response})
        save_memory()
        return full_response
        
    except Exception as e:
        error_msg = "Error de conexión con el cerebro neuronal."
        print(f"[LLM Error] {e}")
        return error_msg

def process_command_with_llm(user_text):
    """
    NLP Router: Analiza la frase del usuario y devuelve un JSON con la intención.
    """
    system_prompt = """You are Jarvis's NLP Router. Analyze the user's voice transcription (which may contain severe phonetic errors in French, Spanish or English).
Output ONLY a valid JSON object. Do not use Markdown blocks (no ```json).

Categories for "intent":
- "PLAY_MUSIC": Wants to listen to music. (e.g. "plait est de bon mâler" -> play Bob Marley)
- "STOP_MUSIC": Wants to stop or pause music.
- "NEXT_MUSIC": Wants to skip to next song.
- "CURRENT_MUSIC": Wants to know what song or music is currently playing right now.
- "WEATHER": Wants to know the weather, temperature, or climate.
- "OPEN_APP": Wants to open an application or program on the computer.
- "BATTERY": Wants to check the laptop battery level.
- "TIMER": Wants to set a timer, alarm, or reminder.
- "CUSTOM_SCRIPT": Wants to run a custom local script like turning off lights, running a project, etc.
- "CHAT": General conversation or anything else.

If intent is "PLAY_MUSIC", include:
- "query": The clean name of the song/artist to search on YouTube. Fix phonetic typos and format it nicely with proper capitalization! (e.g. "bon mâler" -> "Bob Marley").
- "is_playlist": boolean (true if they asked for a playlist/lista/liste).

If intent is "OPEN_APP", include:
- "query": The clean name of the application to open.

If intent is "TIMER", include:
- "duration_seconds": integer representing how many seconds to wait. Convert minutes/hours to seconds.
- "reason": what the timer is for (e.g. "sacar la pizza").

If intent is "CUSTOM_SCRIPT", include:
- "query": the semantic action requested (e.g. "apagar luces").

Examples:
Input: "Mais moi, la plait est de bon mâler."
Output: {"intent": "PLAY_MUSIC", "query": "Bob Marley", "is_playlist": true}

Input: "Arrête la musique"
Output: {"intent": "STOP_MUSIC"}

Input: "Hola como estas"
Output: {"intent": "CHAT"}"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Input: '{user_text}'"}
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.0}
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        content = data.get("message", {}).get("content", "").strip()
        
        # Parse JSON seguro con Regex
        import json
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            content = match.group(0)
            
        return json.loads(content)
    except Exception as e:
        print(f"[LLM Router Error] {e}")
        # Fallback to CHAT
        return {"intent": "CHAT"}

if __name__ == "__main__":
    def on_chunk(text):
        print(text, end="", flush=True)
    print("AXION: ", end="")
    generate_response("Hola Jarvis, ¿cómo estás?", stream_callback=on_chunk)
    print()
