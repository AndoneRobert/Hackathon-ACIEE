import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
import time

# --- LOAD ENV ---
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent
ENV_PATH = ROOT_DIR / ".env"
loaded = load_dotenv(ENV_PATH)

class AIGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # LISTA EXTINSĂ DE MODELE (Failover)
        # Include versiuni specifice care pot ocoli erorile 404 regionale
        self.candidate_models = [
            "gemini-1.5-flash",           # Standard
            "gemini-1.5-flash-001",       # Versiune specifica (deseori merge cand alias-ul nu)
            "gemini-1.5-flash-002",       # Versiune mai noua
            "gemini-1.5-flash-8b",        # Versiune rapida/light
            "gemini-2.0-flash-lite-preview-02-05", # Lite (limite separate)
            "gemini-1.5-pro",
            "gemini-1.5-pro-001",
            "gemini-pro",                 # Legacy 1.0
            "gemini-2.0-flash",           # Experimental (limite mici)
            "gemini-2.5-flash"            # Experimental (limite mici)
        ]

        print(f"--- DEBUG AI GENERATOR ---")
        print(f"API Key gasita: {'DA' if self.api_key else 'NU'}")

        if not self.api_key:
            print("❌ EROARE: GEMINI_API_KEY lipseste!")
        else:
            try:
                genai.configure(api_key=self.api_key)
            except Exception as e:
                print(f"❌ Eroare configurare genai: {e}")

    def get_fallback_questions(self):
        """Intrebari de rezerva (Offline)."""
        print("⚠️ TOATE MODELELE AU ESUAT. FOLOSESC FALLBACK.")
        return [
            {"text": "Care este unitatea minima de informatie?", "options": {"LEFT": "Bit", "RIGHT": "Byte"}, "correct": "LEFT"},
            {"text": "Ce inseamna HTTP?", "options": {"LEFT": "Protocol Transfer", "RIGHT": "High Text"}, "correct": "LEFT"},
            {"text": "Python este un limbaj:", "options": {"LEFT": "Compilat", "RIGHT": "Interpretat"}, "correct": "RIGHT"},
            {"text": "Cine a fondat Microsoft?", "options": {"LEFT": "Steve Jobs", "RIGHT": "Bill Gates"}, "correct": "RIGHT"},
            {"text": "Memoria RAM este:", "options": {"LEFT": "Permanenta", "RIGHT": "Volatila"}, "correct": "RIGHT"},
            {"text": "Ce face CTRL+C?", "options": {"LEFT": "Copiaza", "RIGHT": "Lipeste"}, "correct": "LEFT"}
        ]

    def generate_quiz(self):
        if not self.api_key:
            return self.get_fallback_questions()

        prompt = """
        Genereaza o lista de 6 intrebari trivia despre IT, Programare, Hardware.
        Dificultate: 2 Usoare, 3 Medii, 1 Grea.
        Limba: Romana.
        Format: STRICT JSON ARRAY.
        Schema: [{"text": "Intrebarea?", "options": {"LEFT": "A", "RIGHT": "B"}, "correct": "LEFT"}]
        """

        # Incercam modelele pe rand
        for model_name in self.candidate_models:
            try:
                print(f"🔄 Incerc generare cu: {model_name}...")
                
                config = {}
                # Fortam JSON doar unde stim ca e suportat sigur
                if "1.5" in model_name or "2.0" in model_name or "2.5" in model_name or "flash" in model_name:
                    config = {"response_mime_type": "application/json"}
                
                model = genai.GenerativeModel(model_name, generation_config=config)
                
                # Apelam API-ul
                response = model.generate_content(prompt)
                text_resp = response.text.strip()
                
                if text_resp.startswith("```"):
                    text_resp = text_resp.replace("```json", "").replace("```", "").strip()

                questions = json.loads(text_resp)
                
                if isinstance(questions, list) and len(questions) >= 6:
                    print(f"✅ SUCCES cu modelul {model_name}! {len(questions)} intrebari.")
                    return questions[:6]
            
            except Exception as e:
                # Ignoram erorile si trecem la urmatorul model
                continue

        # Daca am iesit din bucla, inseamna ca niciun model nu a mers
        return self.get_fallback_questions()

if __name__ == "__main__":
    print("\n>>> TEST FAILOVER SYSTEM <<<")
    ai = AIGenerator()
    qs = ai.generate_quiz()
    print("\nREZULTAT FINAL JSON:")
    print(json.dumps(qs, indent=2, ensure_ascii=False))