from backend.app.rag_engine import run_nysc_agent

sid = "debug_sess_1"
res1 = run_nysc_agent("What is the current NYSC allowance?", sid)
print("Q1 Answer:", res1["answer"][:100], "...")

res2 = run_nysc_agent("What is the posting policy?", sid)
print("Q2 Answer:\n", res2["answer"])

