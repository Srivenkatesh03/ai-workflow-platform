import urllib.request
import urllib.error
import json

base_url = "http://localhost:8000/api/v1"

# 1. Login
print("Logging in...")
login_url = f"{base_url}/auth/login"
login_data = json.dumps({
    "email": "test-user-temp-unique@example.com",
    "password": "Password123"
}).encode("utf-8")
req_login = urllib.request.Request(
    login_url,
    data=login_data,
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req_login) as login_resp:
    res = json.loads(login_resp.read().decode())
    token = res["data"]["access_token"]

# 2. Get AI Logs
print("Fetching AI statistics and logs...")
logs_url = f"{base_url}/ai/logs"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}
req_logs = urllib.request.Request(logs_url, headers=headers)

try:
    with urllib.request.urlopen(req_logs) as resp:
        res = json.loads(resp.read().decode())
        print("\nSuccess! Retrieved AI Logs:")
        print(json.dumps(res["data"][:3], indent=2)) # Print first 3 entries
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Body:", e.read().decode())
