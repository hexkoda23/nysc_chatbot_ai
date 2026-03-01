import requests
import json

url = "http://127.0.0.1:8000/api/chat"
headers = {"Content-Type": "application/json"}

r1 = requests.post(url, headers=headers, json={
    "session_id": "test_hist_2", 
    "message": "What is the current NYSC allowance?",
    "selectedLang": "en"
})

r2 = requests.post(url, headers=headers, json={
    "session_id": "test_hist_2", 
    "message": "How do I get my call-up letter?",
    "selectedLang": "en"
})

output = {
    "r1": r1.json().get("answer"),
    "r2": r2.json().get("answer")
}

with open("test_api_out.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

