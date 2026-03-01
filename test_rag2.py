import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.rag_engine import _get_conversation_context, CONVERSATION_HISTORY, _fast_rag_response

sid = "debug_sess_2"
CONVERSATION_HISTORY[sid] = [
    ("What is the current NYSC allowance?", "The current allowance is N77,000 per month.")
]

res = _fast_rag_response("What is the posting policy?", _get_conversation_context(sid))
print("\n--- Answer ---")
print(res["answer"])
print("---------------\n")
