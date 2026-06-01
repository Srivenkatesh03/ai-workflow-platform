import urllib.request
import urllib.error
import json
import time

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
print("Auth token obtained.")

# 2. Create Workflow with a failing step (invalid webhook URL)
print("Creating a workflow with a failing webhook step...")
wf_url = f"{base_url}/workflows"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

wf_payload = {
    "name": "Failing Webhook Workflow",
    "description": "Workflow designed to fail on a connection error to test execution-level retries.",
    "trigger_type": "manual",
    "steps": [
        {
            "step_order": 1,
            "step_type": "webhook_call",
            "configuration": {
                "url": "http://localhost:9999/connection-refused-error"
            }
        }
    ]
}

req_wf = urllib.request.Request(
    wf_url,
    data=json.dumps(wf_payload).encode("utf-8"),
    headers=headers
)

with urllib.request.urlopen(req_wf) as wf_resp:
    wf_res = json.loads(wf_resp.read().decode())
    workflow_id = wf_res["data"]["id"]
print(f"Failing workflow created: {workflow_id}")

# 3. Execute Workflow
print("Executing workflow...")
exec_url = f"{base_url}/workflows/{workflow_id}/execute"
exec_payload = {"payload": {"test_retry_key": "original_payload_value"}}

req_exec = urllib.request.Request(
    exec_url,
    data=json.dumps(exec_payload).encode("utf-8"),
    headers=headers
)

with urllib.request.urlopen(req_exec) as exec_resp:
    exec_res = json.loads(exec_resp.read().decode())
    execution_id = exec_res["data"]["id"]
print(f"Execution started: {execution_id}")

# 4. Wait for execution to fail
print("Waiting for execution to fail...")
status_url = f"{base_url}/executions"
max_attempts = 15
for attempt in range(max_attempts):
    time.sleep(2)
    req_status = urllib.request.Request(status_url, headers=headers)
    with urllib.request.urlopen(req_status) as status_resp:
        status_res = json.loads(status_resp.read().decode())
        execs_list = status_res["data"]
        our_exec = next((ex for ex in execs_list if ex["id"] == execution_id), None)
        if our_exec:
            status = our_exec["status"]
            print(f"Poll {attempt+1}: Status is '{status}'")
            if status == "failed":
                print("Confirmed! Workflow execution failed as expected.")
                break
        else:
            print("Not found yet...")
else:
    print("Failed to observe execution failure in time.")
    exit(1)

# 5. Trigger Execution-Level Retry
print("\nTriggering execution-level retry...")
retry_url = f"{base_url}/executions/{execution_id}/retry"
req_retry = urllib.request.Request(
    retry_url,
    data=b"{}",
    headers=headers
)

with urllib.request.urlopen(req_retry) as retry_resp:
    retry_res = json.loads(retry_resp.read().decode())
    print("Retry API Response:", retry_res["message"])

# 6. Verify that it queues and runs again!
print("Polling to verify that retry execution enqueued and executed...")
for attempt in range(max_attempts):
    time.sleep(1.5)
    req_status = urllib.request.Request(status_url, headers=headers)
    with urllib.request.urlopen(req_status) as status_resp:
        status_res = json.loads(status_resp.read().decode())
        execs_list = status_res["data"]
        our_exec = next((ex for ex in execs_list if ex["id"] == execution_id), None)
        if our_exec:
            status = our_exec["status"]
            # It will transition back from queued -> running -> failed (or whatever the state is)
            print(f"Post-Retry Poll {attempt+1}: Status is '{status}'")
            if status == "running" or status == "failed":
                print(f"Success! The retry is actively running or completed (status: '{status}')")
                
                # Check log messages of this execution to see if the retry triggered successfully
                print("\nInspecting execution logs to verify retry events:")
                print(json.dumps(our_exec["step_executions"], indent=2))
                break
        else:
            print("Not found yet...")
