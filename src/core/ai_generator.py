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
        
        # Modele candidate
        self.candidate_models = [
            "gemini-1.5-flash",           
            "gemini-1.5-flash-001",
            "gemini-2.0-flash",       
            "gemini-1.5-pro",
            "gemini-pro"
        ]

        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
            except Exception as e:
                print(f"❌ Eroare configurare genai: {e}")

    def get_fallback_questions(self):
        # ... (păstrează codul existent pentru quiz) ...
        return [
            {"text": "Unitatea minima de informatie?", "options": {"LEFT": "Bit", "RIGHT": "Byte"}, "correct": "LEFT"},
            {"text": "Ce este CPU?", "options": {"LEFT": "Procesor", "RIGHT": "Memorie"}, "correct": "LEFT"},
            {"text": "Python este:", "options": {"LEFT": "Compilat", "RIGHT": "Interpretat"}, "correct": "RIGHT"},
            {"text": "Fondator Microsoft?", "options": {"LEFT": "Jobs", "RIGHT": "Gates"}, "correct": "RIGHT"},
            {"text": "RAM este:", "options": {"LEFT": "Volatila", "RIGHT": "Permanenta"}, "correct": "LEFT"},
            {"text": "Ctrl+C face:", "options": {"LEFT": "Copy", "RIGHT": "Paste"}, "correct": "LEFT"}
        ]

    def get_fallback_maze(self):
        """Labirintul de rezerva GARANTAT rezolvabil."""
        return [
            "####################",
            "#S  #              #",
            "### # # ########## #",
            "#   # # #        # #",
            "# ### ### ###### # #",
            "# #   #   #      # #",
            "# # ### ### #### # #",
            "# #     #      # # #",
            "# ########### ## # #",
            "#             #   E#",
            "####################"
        ]

    def generate_quiz(self):
        # ... (păstrează codul existent) ...
        if not self.api_key: return self.get_fallback_questions()
        prompt = """Genereaza 6 intrebari trivia IT scurte. JSON Array: [{"text":"...","options":{"LEFT":"...","RIGHT":"..."},"correct":"LEFT"}]"""
        return self._call_gemini(prompt, self.get_fallback_questions, min_items=6)

    def generate_maze(self):
        """Genereaza labirintul cu instructiuni stricte de solvabilitate."""
        if not self.api_key:
            return self.get_fallback_maze()

        # Prompt optimizat pentru logica spatiala
        prompt = """
        Create a 2D Maze layout using ASCII characters.
        Grid size: EXACTLY 20 characters wide, 11 characters tall.
        Characters: '#' (wall), ' ' (empty path), 'S' (Start), 'E' (End).
        
        CRITICAL RULES FOR LOGIC:
        1. Place 'S' at index [1][1] (top-left).
        2. Place 'E' at index [9][18] (bottom-right).
        3. Make sure there is a CLEAR, CONTINUOUS PATH of empty spaces ' ' from 'S' to 'E'.
        4. Do NOT block the path. The maze MUST be solvable.
        5. Outer borders must be '#'.
        
        Output format: STRICT JSON ARRAY of Strings.
        Example: ["####################", "#S  #   ...      #", ...]
        """
        return self._call_gemini(prompt, self.get_fallback_maze, min_items=11)

    def _call_gemini(self, prompt, fallback_func, min_items=1):
        for model_name in self.candidate_models:
            try:
                config = {}
                if "1.5" in model_name or "2.0" in model_name or "flash" in model_name:
                    config = {"response_mime_type": "application/json"}
                
                model = genai.GenerativeModel(model_name, generation_config=config)
                response = model.generate_content(prompt)
                text_resp = response.text.strip()
                
                if text_resp.startswith("```"):
                    text_resp = text_resp.replace("```json", "").replace("```", "").strip()

                data = json.loads(text_resp)
                
                if isinstance(data, list) and len(data) >= min_items:
                    # Validare simpla dimensiuni pentru labirint
                    if min_items == 11: 
                        if len(data[0]) != 20: continue # Latime gresita
                        
                    return data
            except:
                continue

        return fallback_func()