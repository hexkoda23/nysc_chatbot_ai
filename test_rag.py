import sys, os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.rag_engine import run_nysc_agent, CONVERSATION_HISTORY

sid = "debug_sess_1"
res1 = run_nysc_agent("What is the current NYSC allowance?", sid)
print("Q1 Answer:", res1["answer"][:100], "...")

print("\n--- History ---")
print(CONVERSATION_HISTORY.get(sid))
print("---------------\n")

res2 = run_nysc_agent("What is the posting policy?", sid)
print("Q2 Answer:\n", res2["answer"])

