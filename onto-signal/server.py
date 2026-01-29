"""
ONTO Signal Server - Production
"""

import os
import time
import struct
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from streamer import EntropyStreamer, SignalPacket

PORT = int(os.getenv("PORT", "8081"))
SIGNAL_INTERVAL = int(os.getenv("SIGNAL_INTERVAL", "300"))

app = FastAPI(title="ONTO Signal Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

output_dir = Path(os.getenv("SIGNAL_DIR", "./signal"))
key_path = Path(os.getenv("KEY_PATH", "./keys/signing.key"))
streamer = EntropyStreamer(output_dir=str(output_dir), key_path=str(key_path))
current_packet = None

def background_streamer():
    global current_packet
    print(f"[ONTO] Background streamer started (104-byte packets)")
    while True:
        try:
            current_packet = streamer.broadcast()
        except Exception as e:
            print(f"[ONTO] Streamer error: {e}")
        time.sleep(SIGNAL_INTERVAL)

@app.on_event("startup")
async def startup():
    global current_packet
    current_packet = streamer.broadcast()
    print(f"[ONTO] Initial signal generated")
    print(f"[ONTO] Output: {output_dir.absolute()}")
    print(f"[ONTO] Packet size: 104 bytes (8 ts + 32 entropy + 64 sig)")
    thread = threading.Thread(target=background_streamer, daemon=True)
    thread.start()
    print(f"[ONTO] Entropy Streamer started. Interval: {SIGNAL_INTERVAL}s")

@app.get("/")
async def root():
    pk_hex = streamer.verify_key.encode().hex()
    return {"service": "ONTO Signal Server", "version": "1.0.0", "status": "operational", "public_key": pk_hex[:32] + "..."}

@app.get("/health")
async def health():
    return {"status": "healthy" if current_packet else "initializing", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/signal/latest.bin")
async def get_signal_binary():
    if not current_packet:
        return Response(content=b"", status_code=503)
    packet_bytes = current_packet.to_bytes()
    return Response(content=packet_bytes, media_type="application/octet-stream", headers={"Content-Length": str(len(packet_bytes)), "X-Packet-Size": "104"})

@app.get("/signal/latest.json")
async def get_signal_json():
    if not current_packet:
        return {"error": "No signal available"}
    return current_packet.to_dict()

@app.get("/signal/status")
async def get_status():
    if not current_packet:
        return {"status": "initializing"}
    now = int(time.time())
    age = now - current_packet.timestamp
    return {"status": "online", "sigma_id": f"σ_{current_packet.timestamp}", "timestamp": current_packet.timestamp, "age_seconds": age, "next_update_in": max(0, SIGNAL_INTERVAL - age), "packet_size": 104, "entropy_preview": current_packet.entropy[:8].hex()}

@app.get("/signal/verify-key")
async def get_verify_key():
    pk_hex = streamer.verify_key.encode().hex()
    return {"algorithm": "ED25519", "public_key_hex": pk_hex}

if __name__ == "__main__":
    print("=" * 50)
    print("ONTO Signal Server")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
