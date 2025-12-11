import os
import google.generativeai as genai
import traceback
from dotenv import load_dotenv, find_dotenv

# Load .env automatically if present so this script works when run locally
_env = find_dotenv()
if _env:
    load_dotenv(_env)

api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
if not api_key:
    print('No GEMINI_API_KEY or GOOGLE_API_KEY in environment or .env')
    raise SystemExit(1)

print('Configuring genai with provided API key...')
genai.configure(api_key=api_key)

candidates = [
    'gemini-1.5-flash',
    'gemini-1.5',
    'gemini-1.5-pro',
    'gemini-1.5-mini',
    'gemini-1.5-embed',
    'text-bison-001',
    'chat-bison-001',
]

prompt = 'Genereaza 1 intrebare simpla de quiz despre Python in format JSON array.'

methods_model = ['generate_content', 'generate', 'create']
methods_top = ['generate_text', 'generate']

results = []

for mid in candidates:
    print('\n--- Trying model:', mid)
    try:
        # attempt to create model object
        model_obj = None
        try:
            model_obj = genai.GenerativeModel(mid)
            print('Constructed GenerativeModel object for', mid)
        except Exception as e:
            print('Could not construct GenerativeModel:', e)
            model_obj = None

        # Try model methods
        for mname in methods_model:
            if model_obj and hasattr(model_obj, mname):
                func = getattr(model_obj, mname)
                try:
                    print(' Trying model method', mname)
                    try:
                        resp = func(prompt)
                    except TypeError:
                        resp = func(prompt=prompt)
                    print('  Success:', repr(resp)[:200])
                    results.append((mid, 'model.'+mname, 'success', repr(resp)))
                    raise StopIteration
                except Exception as e:
                    print('  Failed:', e)
                    results.append((mid, 'model.'+mname, 'error', str(e)))
        # Try top-level methods
        for mname in methods_top:
            if hasattr(genai, mname):
                func = getattr(genai, mname)
                try:
                    print(' Trying top-level', mname)
                    try:
                        resp = func(model=mid, prompt=prompt)
                    except TypeError:
                        resp = func(mid, prompt)
                    print('  Success:', repr(resp)[:200])
                    results.append((mid, 'top.'+mname, 'success', repr(resp)))
                    raise StopIteration
                except Exception as e:
                    print('  Failed:', e)
                    results.append((mid, 'top.'+mname, 'error', str(e)))
    except StopIteration:
        print('Model', mid, 'worked')
        break
    except Exception as e_outer:
        print('Outer error for', mid, ':', e_outer)
        traceback.print_exc()

print('\n=== RESULTS SUMMARY ===')
for r in results:
    print(r)

print('Done')
