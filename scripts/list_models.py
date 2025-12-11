import os
import google.generativeai as genai
from pprint import pprint
import traceback

try:
    api_key = os.getenv('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    models_iter = genai.list_models()
    print('---MODELS (iterating)---')
    try:
        for m in models_iter:
            # each m may be a dict-like or object depending on library version
            try:
                mid = getattr(m, 'id', None) or m.get('id') if isinstance(m, dict) else str(m)
            except Exception:
                mid = str(m)
            try:
                # print available fields if possible
                methods = getattr(m, 'supported_methods', None)
            except Exception:
                methods = None
            print('MODEL:', mid, ' methods=', methods)
    except Exception as e_iter:
        print('Error iterating models:', e_iter)
        traceback.print_exc()
except Exception as e:
    print('ERROR listing models:')
    print(e)
    traceback.print_exc()
