import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "NYSC_CHATBOT", "backend"))
from app.language import _translate

text = "The current NYSC allowance is N77,000 per month, starting in July 2024 for all serving Corps Members."
translated = _translate(text, target_lang="yo")
print("RESULT:")
print(translated)
