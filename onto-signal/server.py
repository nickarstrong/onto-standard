"""
ONTO Signal Server - Production v1.1
Added: /metrics, request counters, cache headers, uptime
"""

import os
import time
import struct
import threading
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from streamer import EntropyStreamer, SignalPacket

PORT = int(os.getenv("PORT", "8081"))
SIGNAL_INTERVAL = int(os.getenv("SIGNAL_INTERVAL", "300"))

app = FastAPI(title="ONTO Signal Server", version="1.1.0")

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

# === METRICS ===
start_time = time.time()
request_counts = defaultdict(int)
total_requests = 0
total_errors = 0
signals_generated = 0

def background_streamer():
    global current_packet, signals_generated
    print(f"[ONTO] Background streamer started (104-byte packets)")
    while True:
        try:
            current_packet = streamer.broadcast()
            signals_generated += 1
        except Exception as e:
            print(f"[ONTO] Streamer error: {e}")
        time.sleep(SIGNAL_INTERVAL)

@app.middleware("http")
async def count_requests(request: Request, call_next):
    global total_requests, total_errors
    total_requests += 1
    path = request.url.path
    request_counts[path] += 1
    
    response = await call_next(request)
    
    if response.status_code >= 400:
        total_errors += 1
    
    return response

@app.on_event("startup")
async def startup():
    global current_packet, signals_generated
    current_packet = streamer.broadcast()
    signals_generated = 1
    print(f"[ONTO] Initial signal generated")
    print(f"[ONTO] Output: {output_dir.absolute()}")
    print(f"[ONTO] Packet size: 104 bytes (8 ts + 32 entropy + 64 sig)")
    thread = threading.Thread(target=background_streamer, daemon=True)
    thread.start()
    print(f"[ONTO] Entropy Streamer started. Interval: {SIGNAL_INTERVAL}s")

@app.get("/")
async def root():
    pk_hex = streamer.verify_key.encode().hex()
    return {
        "service": "ONTO Signal Server",
        "version": "1.1.0",
        "status": "operational",
        "public_key": pk_hex[:32] + "..."
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy" if current_packet else "initializing",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - start_time)
    }

@app.get("/signal/latest.bin")
async def get_signal_binary():
    if not current_packet:
        return Response(content=b"", status_code=503)
    packet_bytes = current_packet.to_bytes()
    return Response(
        content=packet_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Length": str(len(packet_bytes)),
            "X-Packet-Size": "104",
            "Cache-Control": "no-store, must-revalidate",
            "X-Signal-Timestamp": str(current_packet.timestamp)
        }
    )

@app.get("/signal/latest.json")
async def get_signal_json():
    if not current_packet:
        return {"error": "No signal available"}
    return Response(
        content=str(current_packet.to_dict()).replace("'", '"'),
        media_type="application/json",
        headers={
            "Cache-Control": "no-store, must-revalidate",
            "X-Signal-Timestamp": str(current_packet.timestamp)
        }
    )

@app.get("/signal/status")
async def get_status():
    if not current_packet:
        return {"status": "initializing"}
    now = int(time.time())
    age = now - current_packet.timestamp
    return Response(
        content=str({
            "status": "online",
            "sigma_id": f"σ_{current_packet.timestamp}",
            "timestamp": current_packet.timestamp,
            "age_seconds": age,
            "next_update_in": max(0, SIGNAL_INTERVAL - age),
            "packet_size": 104,
            "entropy_preview": current_packet.entropy[:8].hex()
        }).replace("'", '"'),
        media_type="application/json",
        headers={
            "Cache-Control": "max-age=10"
        }
    )

@app.get("/signal/delayed")
async def get_delayed_signal():
    """Signal with 1-hour delay for OPEN layer"""
    delay_seconds = 3600  # 1 hour
    
    # Find archived signal from ~1 hour ago
    target_ts = int(time.time()) - delay_seconds
    
    # Look for closest archived signal
    archive_files = sorted(output_dir.glob("sigma_*.bin"))
    
    best_file = None
    best_diff = float('inf')
    
    for f in archive_files:
        try:
            ts = int(f.stem.split("_")[1])
            diff = abs(ts - target_ts)
            if diff < best_diff and ts <= target_ts:
                best_diff = diff
                best_file = f
        except (ValueError, IndexError):
            continue
    
    if best_file:
        with open(best_file, 'rb') as f:
            packet_bytes = f.read()
        return Response(
            content=packet_bytes,
            media_type="application/octet-stream",
            headers={
                "Content-Length": str(len(packet_bytes)),
                "X-Packet-Size": "104",
                "Cache-Control": "max-age=3600",
                "X-Signal-Delayed": "true"
            }
        )
    
    # Fallback: return current signal if no archive
    if current_packet:
        return Response(
            content=current_packet.to_bytes(),
            media_type="application/octet-stream",
            headers={
                "X-Signal-Delayed": "false",
                "Cache-Control": "max-age=3600"
            }
        )
    
    return Response(content=b"", status_code=503)

@app.get("/signal/verify-key")
async def get_verify_key():
    pk_hex = streamer.verify_key.encode().hex()
    return {
        "algorithm": "ED25519",
        "public_key_hex": pk_hex,
        "usage": "Verify σ(t) signature with nacl.signing.VerifyKey"
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics"""
    uptime = time.time() - start_time
    
    lines = [
        "# HELP onto_signal_uptime_seconds Server uptime in seconds",
        "# TYPE onto_signal_uptime_seconds gauge",
        f"onto_signal_uptime_seconds {uptime:.0f}",
        "",
        "# HELP onto_signal_requests_total Total HTTP requests",
        "# TYPE onto_signal_requests_total counter",
        f"onto_signal_requests_total {total_requests}",
        "",
        "# HELP onto_signal_errors_total Total HTTP errors (4xx, 5xx)",
        "# TYPE onto_signal_errors_total counter",
        f"onto_signal_errors_total {total_errors}",
        "",
        "# HELP onto_signal_signals_generated_total Total signals generated",
        "# TYPE onto_signal_signals_generated_total counter",
        f"onto_signal_signals_generated_total {signals_generated}",
        "",
        "# HELP onto_signal_interval_seconds Signal broadcast interval",
        "# TYPE onto_signal_interval_seconds gauge",
        f"onto_signal_interval_seconds {SIGNAL_INTERVAL}",
        "",
        "# HELP onto_signal_packet_size_bytes Signal packet size",
        "# TYPE onto_signal_packet_size_bytes gauge",
        "onto_signal_packet_size_bytes 104",
        "",
        "# HELP onto_signal_requests_by_path Requests by endpoint",
        "# TYPE onto_signal_requests_by_path counter",
    ]
    
    for path, count in sorted(request_counts.items()):
        safe_path = path.replace('"', '\\"')
        lines.append(f'onto_signal_requests_by_path{{path="{safe_path}"}} {count}')
    
    return Response(
        content="\n".join(lines) + "\n",
        media_type="text/plain; charset=utf-8"
    )

@app.get("/stats")
async def get_stats():
    """JSON stats for dashboard"""
    uptime = time.time() - start_time
    
    return {
        "uptime_seconds": int(uptime),
        "uptime_human": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
        "total_requests": total_requests,
        "total_errors": total_errors,
        "error_rate": round(total_errors / max(total_requests, 1) * 100, 2),
        "signals_generated": signals_generated,
        "signal_interval": SIGNAL_INTERVAL,
        "requests_per_minute": round(total_requests / max(uptime / 60, 1), 2),
        "top_endpoints": dict(sorted(request_counts.items(), key=lambda x: -x[1])[:5])
    }

if __name__ == "__main__":
    print("=" * 50)
    print("ONTO Signal Server v1.1")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
