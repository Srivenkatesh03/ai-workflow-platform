import urllib.request
import urllib.error
import json

base_url = "http://localhost:8000/api/v1"

# Login
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

# Make post with short name "A"
wf_url = f"{base_url}/workflows"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

payload = {
    "name": "A",
    "description": "Test description",
    "trigger_type": "manual",
    "steps": []
}

req_wf = urllib.request.Request(
    wf_url,
    data=json.dumps(payload).encode("utf-8"),
    headers=headers
)

try:
    with urllib.request.urlopen(req_wf) as response:
        print("Success:", response.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    body = e.read().decode()
    print("Body:", body)
    print("Length of body:", len(body))
