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
client_errors = 0  # 4xx - client's fault
server_errors = 0  # 5xx - our fault
signals_generated = 0
is_paused = False

# === ADMIN ===
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "")

def background_streamer():
    global current_packet, signals_generated
    print(f"[ONTO] Background streamer started (104-byte packets)")
    while True:
        try:
            if not is_paused:
                current_packet = streamer.broadcast()
                signals_generated += 1
            else:
                print("[ONTO] Skipping broadcast (paused)")
        except Exception as e:
            print(f"[ONTO] Streamer error: {e}")
        time.sleep(SIGNAL_INTERVAL)

@app.middleware("http")
async def count_requests(request: Request, call_next):
    global total_requests, client_errors, server_errors
    
    path = request.url.path
    
    # Skip counting for keep-alive ping
    if path == "/ping":
        return await call_next(request)
    
    total_requests += 1
    request_counts[path] += 1
    
    response = await call_next(request)
    
    # Separate client errors (4xx) from server errors (5xx)
    if 400 <= response.status_code < 500:
        client_errors += 1
    elif response.status_code >= 500:
        server_errors += 1
    
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

@app.get("/ping")
async def ping():
    """Keep-alive endpoint (not counted in stats)"""
    return Response(content="pong", media_type="text/plain")

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
        "# HELP onto_signal_client_errors_total Client errors (4xx)",
        "# TYPE onto_signal_client_errors_total counter",
        f"onto_signal_client_errors_total {client_errors}",
        "",
        "# HELP onto_signal_server_errors_total Server errors (5xx)",
        "# TYPE onto_signal_server_errors_total counter",
        f"onto_signal_server_errors_total {server_errors}",
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
    
    # Error rate based on SERVER errors only (5xx), not client errors (4xx)
    server_error_rate = round(server_errors / max(total_requests, 1) * 100, 2)
    
    return {
        "uptime_seconds": int(uptime),
        "uptime_human": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m",
        "total_requests": total_requests,
        "client_errors": client_errors,
        "server_errors": server_errors,
        "error_rate_percent": server_error_rate,  # Only 5xx errors
        "signals_generated": signals_generated,
        "signal_interval": SIGNAL_INTERVAL,
        "requests_per_minute": round(total_requests / max(uptime / 60, 1), 2),
        "top_endpoints": dict(sorted(request_counts.items(), key=lambda x: -x[1])[:5])
    }

# === ADMIN ENDPOINTS ===
def require_admin(request: Request):
    """Check admin auth"""
    if not ADMIN_SECRET:
        return False, "ADMIN_SECRET not configured"
    
    provided = request.headers.get("X-Admin-Key", "")
    if provided != ADMIN_SECRET:
        return False, "Invalid admin key"
    
    return True, None

@app.get("/signal/history")
async def get_signal_history(limit: int = 10):
    """Get last N signals from archive"""
    if limit > 50:
        limit = 50
    
    archive_files = sorted(output_dir.glob("sigma_*.bin"), reverse=True)[:limit]
    
    history = []
    for f in archive_files:
        try:
            ts = int(f.stem.split("_")[1])
            with open(f, 'rb') as file:
                data = file.read()
            packet = SignalPacket.from_bytes(data)
            history.append({
                "timestamp": packet.timestamp,
                "timestamp_iso": datetime.utcfromtimestamp(packet.timestamp).isoformat() + "Z",
                "sigma_id": f"σ_{packet.timestamp}",
                "entropy_preview": packet.entropy[:8].hex(),
                "file": f.name
            })
        except Exception as e:
            continue
    
    return {
        "count": len(history),
        "limit": limit,
        "signals": history
    }

@app.post("/signal/verify")
async def verify_signal(request: Request):
    """Verify a signal packet signature"""
    body = await request.body()
    
    if len(body) != 104:
        return {"valid": False, "error": f"Invalid packet size: {len(body)}, expected 104"}
    
    try:
        packet = SignalPacket.from_bytes(body)
        
        # Reconstruct header and verify
        header = struct.pack(">Q", packet.timestamp) + packet.entropy
        
        try:
            streamer.verify_key.verify(header, packet.signature)
            return {
                "valid": True,
                "timestamp": packet.timestamp,
                "timestamp_iso": datetime.utcfromtimestamp(packet.timestamp).isoformat() + "Z",
                "entropy_preview": packet.entropy[:8].hex()
            }
        except Exception:
            return {"valid": False, "error": "Signature verification failed"}
    
    except Exception as e:
        return {"valid": False, "error": str(e)}

@app.get("/admin/status")
async def admin_status(request: Request):
    """Full system status (admin only)"""
    ok, err = require_admin(request)
    if not ok:
        return Response(content=f'{{"error": "{err}"}}', status_code=401, media_type="application/json")
    
    uptime = time.time() - start_time
    archive_count = len(list(output_dir.glob("sigma_*.bin")))
    
    # Error rate based on SERVER errors only (5xx)
    server_error_rate = round(server_errors / max(total_requests, 1) * 100, 2)
    
    return {
        "paused": is_paused,
        "uptime_seconds": int(uptime),
        "signal_interval": SIGNAL_INTERVAL,
        "signals_generated": signals_generated,
        "archive_count": archive_count,
        "total_requests": total_requests,
        "client_errors": client_errors,
        "server_errors": server_errors,
        "error_rate_percent": server_error_rate,  # Only 5xx
        "current_signal": current_packet.to_dict() if current_packet else None,
        "output_dir": str(output_dir.absolute()),
        "public_key": streamer.verify_key.encode().hex()
    }

@app.post("/admin/pause")
async def admin_pause(request: Request):
    """Pause signal generation"""
    global is_paused
    ok, err = require_admin(request)
    if not ok:
        return Response(content=f'{{"error": "{err}"}}', status_code=401, media_type="application/json")
    
    is_paused = True
    print("[ONTO] Signal generation PAUSED by admin")
    return {"status": "paused", "message": "Signal generation paused"}

@app.post("/admin/resume")
async def admin_resume(request: Request):
    """Resume signal generation"""
    global is_paused
    ok, err = require_admin(request)
    if not ok:
        return Response(content=f'{{"error": "{err}"}}', status_code=401, media_type="application/json")
    
    is_paused = False
    print("[ONTO] Signal generation RESUMED by admin")
    return {"status": "running", "message": "Signal generation resumed"}

@app.post("/admin/broadcast")
async def admin_force_broadcast(request: Request):
    """Force generate new signal immediately"""
    global current_packet, signals_generated
    ok, err = require_admin(request)
    if not ok:
        return Response(content=f'{{"error": "{err}"}}', status_code=401, media_type="application/json")
    
    current_packet = streamer.broadcast()
    signals_generated += 1
    print("[ONTO] Forced broadcast by admin")
    return {
        "status": "broadcasted",
        "signal": current_packet.to_dict()
    }

@app.post("/admin/clear-archive")
async def admin_clear_archive(request: Request, keep_last: int = 10):
    """Clear old archive files, keep last N"""
    ok, err = require_admin(request)
    if not ok:
        return Response(content=f'{{"error": "{err}"}}', status_code=401, media_type="application/json")
    
    archive_files = sorted(output_dir.glob("sigma_*.bin"), reverse=True)
    
    deleted = 0
    for f in archive_files[keep_last:]:
        try:
            f.unlink()
            deleted += 1
        except:
            pass
    
    print(f"[ONTO] Admin cleared archive: {deleted} files deleted, {keep_last} kept")
    return {"deleted": deleted, "kept": keep_last}

@app.get("/info")
async def get_info():
    """Full server information for SDK/docs"""
    return {
        "service": "ONTO Signal Server",
        "version": "1.1.0",
        "protocol": "ONTO Standard Protocol v1",
        "packet": {
            "size_bytes": 104,
            "structure": "8 (timestamp u64 BE) + 32 (entropy) + 64 (Ed25519 signature)"
        },
        "crypto": {
            "signature": "Ed25519",
            "entropy": "os.urandom (CSPRNG)",
            "public_key": streamer.verify_key.encode().hex()
        },
        "timing": {
            "interval_seconds": SIGNAL_INTERVAL,
            "archive_retention_hours": 48
        },
        "endpoints": {
            "signal": ["/signal/latest.bin", "/signal/latest.json", "/signal/status", "/signal/delayed", "/signal/history", "/signal/verify"],
            "info": ["/", "/health", "/info", "/metrics", "/stats"],
            "admin": ["/admin/status", "/admin/pause", "/admin/resume", "/admin/broadcast", "/admin/clear-archive"]
        }
    }

if __name__ == "__main__":
    print("=" * 50)
    print("ONTO Signal Server v1.1")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
