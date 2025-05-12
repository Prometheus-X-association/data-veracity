from fastapi import FastAPI, Request, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Dict, Any
import time
import asyncio
import json
import requests

app = FastAPI()
queue = asyncio.Queue()

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    html = Path("static/index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)

@app.post("/webhooks/test")
async def webhook_test():
    print("Webhook test received!")
    return {"ok": True}

@app.post("/webhooks/topic/{topic}/")
async def webhook_handler(topic: str, request: Request):
    payload = await request.json()
    print(f"[CONSUMER] Webhook received on topic: {topic}")
    print(json.dumps(payload, indent=2))
    time.sleep(1)
    await queue.put(payload)
    return {"status": "ok"}

@app.post("/receive_vc")
async def receive_vc(payload: Dict[str, Any]):
    print("Received forwarded VC from infrastructure:")
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
    subject: str = Query("ConsumerApp"),
    issuer_id: str = Query("dva-consumer"),
    comment: str = Query("Requested dynamically")
):
    try:
        params = {
            "subject": subject,
            "issuer_id": issuer_id,
            "comment": comment,
            "target": "consumer"
        }
        print("Requesting VC from infrastructure with params:", params)
        response = requests.post("http://dva-acapy-controller-infrastructure:8051/generate_aov", params=params)
        response.raise_for_status()
        response_data = response.json()
        print("Received response from infrastructure:", response_data)

        vc_data = response_data.get("credential_data", {})
        await queue.put(vc_data)
        return {"received_vc": vc_data}
    except Exception as e:
        print(f"VC request failed: {e}")
        return {"error": str(e)}
