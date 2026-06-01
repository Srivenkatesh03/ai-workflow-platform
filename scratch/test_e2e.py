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
print("Auth token obtained successfully.")

# 2. Create Workflow with AI steps
print("Creating E2E Workflow with AI Summarize & AI Classify steps...")
wf_url = f"{base_url}/workflows"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

wf_payload = {
    "name": "E2E AI Analysis Workflow",
    "description": "Automatically analyzes incident alerts using sequential summarization and classification.",
    "trigger_type": "manual",
    "steps": [
        {
            "step_order": 1,
            "step_type": "ai_summarize",
            "configuration": {
                "text": "{{ payload.text }}"
            }
        },
        {
            "step_order": 2,
            "step_type": "ai_classify",
            "configuration": {
                "text": "{{ steps.ai_summarize.summary }}",
                "labels": ["urgent", "normal", "low"]
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
    workflow = wf_res["data"]
    workflow_id = workflow["id"]
print(f"Workflow created successfully with ID: {workflow_id}")

# 3. Execute the Workflow
print("Executing the workflow with test payload...")
exec_url = f"{base_url}/workflows/{workflow_id}/execute"
exec_payload = {
    "payload": {
        "text": "URGENT SYSTEM ALARM: Database memory utilization has exceeded 95%! Memory leak suspected in transaction pool. Inform the DevOps team immediately."
    }
}

req_exec = urllib.request.Request(
    exec_url,
    data=json.dumps(exec_payload).encode("utf-8"),
    headers=headers
)

with urllib.request.urlopen(req_exec) as exec_resp:
    exec_res = json.loads(exec_resp.read().decode())
    execution = exec_res["data"]
    execution_id = execution["id"]
print(f"Workflow execution enqueued successfully. Execution ID: {execution_id}")

# 4. Poll execution status
print("Polling execution status (waiting for Celery task processing)...")
status_url = f"{base_url}/executions" # lists all or gets details?
# Let's poll by getting the list and finding our execution, or let's verify if there is a detailed endpoint.
# Since list_executions lists all, we can poll that!

max_attempts = 15
for attempt in range(max_attempts):
    time.sleep(2)
    req_status = urllib.request.Request(status_url, headers=headers)
    with urllib.request.urlopen(req_status) as status_resp:
        status_res = json.loads(status_resp.read().decode())
        execs_list = status_res["data"]
        
        # Find our execution
        our_exec = next((ex for ex in execs_list if ex["id"] == execution_id), None)
        if our_exec:
            status = our_exec["status"]
            print(f"Attempt {attempt+1}: Status is '{status}'")
            if status in ["completed", "failed"]:
                print(f"\nExecution finished! Final status: {status.upper()}")
                print(json.dumps(our_exec, indent=2))
                break
        else:
            print("Execution not found in ledger list yet...")
else:
    print("Polling timed out! Celery task might be taking longer to boot or process.")
