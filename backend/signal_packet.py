"""
ONTO Signal Packet Generator
Генерирует 104-байтные σ(t) пакеты для Signal Server.

Packet format (104 bytes):
  [0..8]    timestamp   u64 BE
  [8..40]   entropy     32 bytes (SHA256 от seed + timestamp)
  [40..104] signature   64 bytes (HMAC-SHA256 + padding)

Интеграция: добавить эти эндпоинты в Signal Server (onto-signal).
"""

import struct
import hashlib
import hmac
import time
import os
import secrets

# ============ Конфигурация ============

# Секретный ключ сервера (менять на production!)
SIGNAL_SECRET = os.environ.get("ONTO_SIGNAL_SECRET", "onto-signal-dev-key-change-in-production")

# Интервал ротации σ(t) в секундах (1 час)
ROTATION_INTERVAL = 3600


class SignalPacketGenerator:
    """Генератор 104-байтных σ(t) пакетов."""
    
    def __init__(self, secret: str = SIGNAL_SECRET):
        self.secret = secret.encode('utf-8')
        self._current_packet: bytes | None = None
        self._current_timestamp: int = 0
    
    def generate(self) -> bytes:
        """Генерирует новый 104-байтный пакет."""
        now = int(time.time())
        
        # Используем slot (округлённый timestamp) для consistency
        slot = now - (now % ROTATION_INTERVAL)
        
        # Если текущий пакет ещё актуален — возвращаем кэш
        if self._current_packet and self._current_timestamp == slot:
            return self._current_packet
        
        # 1. Timestamp (8 bytes, big-endian)
        timestamp_bytes = struct.pack('>Q', slot)
        
        # 2. Entropy (32 bytes) = SHA256(secret + slot + random_seed)
        # random_seed меняется каждый slot, но детерминированно для одного slot
        seed_material = self.secret + timestamp_bytes + b"onto_entropy_v1"
        entropy = hashlib.sha256(seed_material).digest()
        
        # 3. Signature (64 bytes) = HMAC-SHA256(secret, timestamp + entropy) + padding
        signable = timestamp_bytes + entropy  # 40 bytes
        sig_hmac = hmac.new(self.secret, signable, hashlib.sha256).digest()  # 32 bytes
        
        # Расширяем до 64 байт (имитация ED25519 размера)
        # В production: реальная ED25519 подпись
        padding_material = self.secret + sig_hmac + b"padding_v1"
        sig_padding = hashlib.sha256(padding_material).digest()  # ещё 32 bytes
        signature = sig_hmac + sig_padding  # 64 bytes
        
        # Собираем пакет
        packet = timestamp_bytes + entropy + signature
        assert len(packet) == 104, f"Packet size error: {len(packet)}"
        
        # Кэшируем
        self._current_packet = packet
        self._current_timestamp = slot
        
        return packet
    
    def verify(self, packet: bytes) -> bool:
        """Верифицирует пакет (серверная проверка)."""
        if len(packet) != 104:
            return False
        
        timestamp_bytes = packet[0:8]
        entropy = packet[8:40]
        signature = packet[40:104]
        
        # Пересчитываем entropy
        seed_material = self.secret + timestamp_bytes + b"onto_entropy_v1"
        expected_entropy = hashlib.sha256(seed_material).digest()
        
        if entropy != expected_entropy:
            return False
        
        # Пересчитываем подпись
        signable = timestamp_bytes + entropy
        expected_hmac = hmac.new(self.secret, signable, hashlib.sha256).digest()
        
        if signature[:32] != expected_hmac:
            return False
        
        return True
    
    def parse(self, packet: bytes) -> dict:
        """Парсит пакет в человекочитаемый формат."""
        if len(packet) != 104:
            raise ValueError(f"Invalid packet: {len(packet)} bytes")
        
        timestamp = struct.unpack('>Q', packet[0:8])[0]
        entropy = packet[8:40]
        signature = packet[40:104]
        
        return {
            "timestamp": timestamp,
            "sigma_id": f"σ_{timestamp}",
            "entropy_hex": entropy.hex()[:16] + "...",
            "signature_hex": signature.hex()[:16] + "...",
            "valid": self.verify(packet),
            "size": 104,
        }


# ============ FastAPI эндпоинты (для Signal Server) ============

"""
Добавить в onto-signal/server.py (или main.py):

from signal_packet import SignalPacketGenerator

generator = SignalPacketGenerator()

@app.get("/signal/latest.bin")
async def signal_latest_bin():
    packet = generator.generate()
    return Response(
        content=packet,
        media_type="application/octet-stream",
        headers={
            "Content-Length": "104",
            "X-Sigma-Id": f"σ_{struct.unpack('>Q', packet[0:8])[0]}",
            "Cache-Control": "public, max-age=300",  # 5 min cache
        }
    )

@app.get("/signal/latest")
async def signal_latest_json():
    packet = generator.generate()
    info = generator.parse(packet)
    return info

@app.get("/signal/verify")
async def signal_verify(packet_hex: str):
    packet = bytes.fromhex(packet_hex)
    return {"valid": generator.verify(packet)}
"""


if __name__ == "__main__":
    gen = SignalPacketGenerator()
    
    # Генерируем пакет
    packet = gen.generate()
    print(f"Packet: {len(packet)} bytes")
    print(f"Parsed: {gen.parse(packet)}")
    print(f"Verified: {gen.verify(packet)}")
    
    # Hex для отладки
    print(f"\nHex dump:")
    print(f"  Timestamp: {packet[0:8].hex()}")
    print(f"  Entropy:   {packet[8:40].hex()}")
    print(f"  Signature: {packet[40:104].hex()}")
