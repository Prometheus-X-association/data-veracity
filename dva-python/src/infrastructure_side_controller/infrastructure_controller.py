from typing import List, Dict, Any
from fastapi import FastAPI, Request, Body, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from aov import AOV, Evaluation
from datetime import datetime

import uvicorn
import requests
import json
import uuid
import time
import os
import httpx

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

LOG_FILE = "log.json"
webhook_logs = []

SELF_CONNECTION_ID = None
SELF_SCHEMA_ID = None
SELF_CRED_DEF_ID = None

ADMIN_URL = "http://dva-acapy-wallet-infrastructure:8031"
ADMIN_LABEL = "dva-infrastructure"

@app.on_event("startup")
async def startup_event():
    print("Infrastructure Controller is starting...")

@app.on_event("shutdown")
async def shutdown_event():
    print("Infrastructure Controller is shutting down...")

    if webhook_logs:
        with open("log_human_readable.json", "w") as f:
            json.dump(webhook_logs, f, indent=2)

@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Helper function: wait until connection is active
def wait_until_connection_active(admin_url, conn_id, timeout=10):
    for _ in range(timeout):
        conns = requests.get(f"{admin_url}/connections").json()["results"]
        conn = next((c for c in conns if c["connection_id"] == conn_id), None)
        if conn and conn["state"] == "active":
            return True
        time.sleep(1)
    return False

@app.post("/webhooks/topic/{topic}/")
async def webhook_listener(topic: str, request: Request):
    data = await request.json()
    webhook_logs.append({"topic": topic, "data": data})

    with open(LOG_FILE, "w") as f:
        json.dump(webhook_logs, f, indent=2)

    if topic == "issue_credential_v2_0":
        state = data.get("state")
        cred_id = data.get("cred_ex_record", {}).get("cred_ex_id", "N/A")
        conn_id = data.get("cred_ex_record", {}).get("connection_id", "N/A")
        print(f"VC Issuance Webhook - State: {state} | Cred ID: {cred_id} | Conn ID: {conn_id}")

        with open("vc_issuance_log.json", "a") as log:
            log.write(json.dumps({
                "state": state,
                "cred_id": cred_id,
                "conn_id": conn_id,
                "raw": data
            }, indent=2) + ",\n")

    print(f"Webhook received on topic: {topic}")
    return {"status": "received"}


# Root endpoint
@app.get("/")
async def index():
    return {"message": "Infrastructure Controller is running."}

# Create connection from infrastructure to consumer
@app.post("/connect_infrastructure_consumer")
async def connect_infrastructure_consumer():
    invitation_response = requests.post("http://dva-acapy-wallet-infrastructure:8031/out-of-band/create-invitation", json={
        "handshake_protocols": ["https://didcomm.org/didexchange/1.0"],
        "use_public_did": False
    })

    if invitation_response.status_code != 200:
        return {"error": "Failed to create invitation", "details": invitation_response.text}

    invitation = invitation_response.json()["invitation"]

    receive_response = requests.post("http://dva-acapy-wallet-consumer:8032/out-of-band/receive-invitation", json=invitation)

    if receive_response.status_code != 200:
        return {"error": "Consumer failed to receive invitation", "details": receive_response.text}

    return {"message": "Connection created between infrastructure and consumer"}

@app.get("/connections/self")
async def get_self_connection():
    global SELF_CONNECTION_ID

    if not SELF_CONNECTION_ID:
        return {"error": "Self-connection not initialized."}

    return {"self_connection_id": SELF_CONNECTION_ID}

@app.post("/init_all_self")
async def init_all_self():
    global SELF_CONNECTION_ID, SELF_SCHEMA_ID, SELF_CRED_DEF_ID

    # Step 1: Create Invitation for self-connection
    invitation_resp = requests.post(f"{ADMIN_URL}/out-of-band/create-invitation", json={
        "handshake_protocols": ["https://didcomm.org/didexchange/1.0"],
        "use_public_did": False
    })
    if invitation_resp.status_code != 200:
        return {"error": "Failed to create self-invitation", "details": invitation_resp.text}

    invitation = invitation_resp.json()["invitation"]

    # Step 2: Receive own invitation
    receive_resp = requests.post(f"{ADMIN_URL}/out-of-band/receive-invitation", json=invitation)
    if receive_resp.status_code != 200:
        return {"error": "Failed to accept own invitation", "details": receive_resp.text}

    conn_id = receive_resp.json()["connection_id"]

    if not wait_until_connection_active(ADMIN_URL, conn_id):
        return {"error": "Self connection did not become active"}

    SELF_CONNECTION_ID = conn_id

    # Step 3: Create Self-Identity Schema
    schema_resp = requests.post(f"{ADMIN_URL}/schemas", json={
        "schema_name": f"Self-Identity-{uuid.uuid4().hex[:6]}",
        "schema_version": "1.0",
        "attributes": ["vc_id", "valid_since", "subject", 
                       "issuer_id", "record_id", 
                       "contract_id", "evaluations"]
    })
    if schema_resp.status_code != 200:
        return {"error": "Failed to create Self-Identity schema", "details": schema_resp.text}

    SELF_SCHEMA_ID = schema_resp.json().get("schema_id")

    # Step 4: Create Credential Definition
    cred_def_resp = requests.post(f"{ADMIN_URL}/credential-definitions", json={
        "schema_id": SELF_SCHEMA_ID,
        "support_revocation": False,
        "tag": "self-identity"
    })
    if cred_def_resp.status_code != 200:
        return {"error": "Failed to create Self-Identity credential definition", "details": cred_def_resp.text}

    SELF_CRED_DEF_ID = cred_def_resp.json().get("credential_definition_id")

    with open("cred_def.txt", "w") as f:
        json.dump({"cred_def_id": SELF_CRED_DEF_ID}, f)

    return {"message": "Self-connection, schema, and credential definition initialized successfully."}

def parse_evaluation_comment(comment: str) -> List[Dict[str, Any]]:
    """
    "lorem: ipsum ; sit : amet ; dolor: sit amet"
    -> [{"lorem": "ipsum"}, {"sit": "amet"}, {"dolor": "sit amet"}]
    """
    entries = [entry.strip() for entry in comment.split(';') if ':' in entry]
    parsed = []
    for entry in entries:
        try:
            key, value = [x.strip() for x in entry.split(':', 1)]
            parsed.append({key: value})
        except ValueError:
            continue
    return parsed

@app.post("/generate_aov")
async def generate_aov(
    subject: str = Query(...),
    issuer_id: str = Query(...),
    comment: str = Query("Requested by consumer"),
    target: str = Query("self", enum=["self", "consumer"])
):
    global SELF_CONNECTION_ID, SELF_CRED_DEF_ID

    parsed_eval = parse_evaluation_comment(comment)
    record = AOV(
        vc_id=str(uuid.uuid4()),
        valid_since=datetime.utcnow(),
        subject=subject,
        issuer_id=issuer_id,
        record_id=str(uuid.uuid4()),
        contract_id=uuid.uuid4().hex,
        evaluations=Evaluation(eval=parsed_eval)
    )

    if target not in ["self", "consumer"]:
        raise HTTPException(status_code=400, detail="Invalid target")

    if target == "self":
        if not SELF_CONNECTION_ID or not SELF_CRED_DEF_ID:
            raise HTTPException(status_code=400, detail="Self connection or credential definition not initialized")
        connection_id = SELF_CONNECTION_ID
        cred_def_id = SELF_CRED_DEF_ID
    else:
        conns = requests.get(f"{ADMIN_URL}/connections").json()["results"]
        consumer_conn = next((c for c in conns if c["connection_id"] != SELF_CONNECTION_ID), None)
        if not consumer_conn:
            raise HTTPException(status_code=400, detail="No consumer connection found")
        connection_id = consumer_conn["connection_id"]

        try:
            with open("cred_def.txt", "r") as f:
                cred_def_data = json.load(f)
            cred_def_id = cred_def_data["cred_def_id"]
        except Exception:
            raise HTTPException(status_code=500, detail="Missing or invalid credential definition file")

    cred_attrs = {
        "vc_id": record.vc_id,
        "valid_since": record.valid_since.isoformat(),
        "subject": record.subject,
        "issuer_id": record.issuer_id,
        "record_id": record.record_id,
        "contract_id": record.contract_id,
        "evaluations": record.evaluations.json()
    }

    issue_payload = {
        "connection_id": connection_id,
        "credential_preview": {
            "@type": "issue-credential/2.0/credential-preview",
            "attributes": [{"name": k, "value": v} for k, v in cred_attrs.items()]
        },
        "filter": {
            "indy": {
                "cred_def_id": cred_def_id
            }
        }
    }

    issue_resp = requests.post(f"{ADMIN_URL}/issue-credential-2.0/send", json=issue_payload)

    if issue_resp.status_code != 200:
        return {"error": "Credential issue failed", "details": issue_resp.text}

    if target == "consumer":
        try:
            forward_resp = requests.post(
                "http://dva-acapy-controller-consumer:8052/receive_vc",
                json={"source": "infrastructure", "credential": cred_attrs}
            )
            forward_resp.raise_for_status()
            print("Forwarded VC to consumer UI stream.")
        except Exception as e:
            print(f"Failed to forward VC to consumer UI: {e}")
    return {"message": f"Custom VC issued to {target}", "credential_data": cred_attrs}


@app.post("/receive_vc")
async def receive_vc(payload: Dict[str, Any]):
    print("Received forwarded VC from provider:")
    print(json.dumps(payload, indent=2))
    time.sleep(1)
    await queue.put(payload)
    return {"status": "ok"}

@app.get("/stream")
async def stream():
    async def event_generator():
        while True:
            data = await queue.get()
            yield f"data: {json.dumps(data)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/request_aov")
async def request_aov(
    subject: str = Query("InfrastructureApp"),
    issuer_id: str = Query("dva-infrastructure"),
    comment: str = Query("Requested dynamically")
):
    try:
        params = {
            "subject": subject,
            "issuer_id": issuer_id,
            "comment": comment,
            "target": "consumer"
        }
        print("Requesting VC from provider with params:", params)
        response = requests.post("http://dva-acapy-controller-provider:8051/generate_aov", params=params)
        response.raise_for_status()
        response_data = response.json()
        print("Received response from provider:", response_data)

        vc_data = response_data.get("credential_data", {})
        await queue.put(vc_data)
        return {"received_vc": vc_data}
    except Exception as e:
        print(f"VC request failed: {e}")
        return {"error": str(e)}
