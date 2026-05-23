from backend.app.language import translate_texts

text = "The current NYSC allowance is N77,000 per month, starting in July 2024 for all serving Corps Members."
translated = translate_texts([text], target_lang="yo")[0]
print("RESULT:")
print(translated)
