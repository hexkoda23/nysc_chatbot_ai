from backend.app.database import insert_message, upsert_conversation
from backend.app.rag_engine import run_nysc_agent

sid = "debug_sess_2"
upsert_conversation(sid, "Debug session")
insert_message(sid, "user", "How can I apply for NYSC relocation?")
first = run_nysc_agent("How can I apply for NYSC relocation?", sid)
insert_message(sid, "assistant", first["answer"], first.get("sources", []))
insert_message(sid, "user", "What are the steps?")

res = run_nysc_agent("What are the steps?", sid)
print("\n--- Answer ---")
print(res["answer"])
print("---------------\n")
