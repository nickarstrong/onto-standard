# ONTO Entropy Streamer
# Генерирует и публикует σ(t) сигнал
# Signal Packet: 104 bytes (8 timestamp + 32 entropy + 64 signature)

import os
import time
import json
import struct
from datetime import datetime
from pathlib import Path

# Для подписи ED25519 (PyNaCl)
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

class SignalPacket:
    """
    104-байтный пакет сигнала:
    - timestamp: 8 bytes (u64 BE)
    - entropy: 32 bytes
    - signature: 64 bytes (ED25519)
    """
    
    def __init__(self, timestamp: int, entropy: bytes, signature: bytes):
        self.timestamp = timestamp
        self.entropy = entropy
        self.signature = signature
    
    def to_bytes(self) -> bytes:
        """Сериализация в 104 байта"""
        return struct.pack(">Q", self.timestamp) + self.entropy + self.signature
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "SignalPacket":
        """Парсинг из 104 байт"""
        if len(data) != 104:
            raise ValueError(f"Invalid packet size: {len(data)}")
        
        timestamp = struct.unpack(">Q", data[0:8])[0]
        entropy = data[8:40]
        signature = data[40:104]
        
        return cls(timestamp, entropy, signature)
    
    def to_dict(self) -> dict:
        """JSON-представление для отладки"""
        return {
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.utcfromtimestamp(self.timestamp).isoformat() + "Z",
            "sigma_id": f"σ_{self.timestamp}",
            "entropy_hex": self.entropy.hex(),
            "entropy_hash": self.entropy[:8].hex(),  # Короткий ID
            "signature_hex": self.signature.hex(),
        }


class EntropyStreamer:
    def __init__(self, output_dir: str = "./signal", key_path: str = "./keys/signing.key"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем или генерируем ключ подписи
        self.key_path = Path(key_path)
        self.signing_key = self._load_or_create_key()
        
        # Публичный ключ для верификации (распространяется клиентам)
        self.verify_key = self.signing_key.verify_key
        print(f"[ONTO] Public Key (hex): {self.verify_key.encode(HexEncoder).decode()}")
    
    def _load_or_create_key(self) -> SigningKey:
        """Загружает существующий ключ или создаёт новый"""
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.key_path.exists():
            with open(self.key_path, 'rb') as f:
                seed = f.read()
            print(f"[ONTO] Loaded existing signing key")
            return SigningKey(seed)
        else:
            key = SigningKey.generate()
            with open(self.key_path, 'wb') as f:
                f.write(bytes(key))
            print(f"[ONTO] Generated new signing key")
            return key
    
    def generate_packet(self) -> SignalPacket:
        """Генерирует новый 104-байтный пакет"""
        
        # 1. Временная метка (UNIX timestamp)
        timestamp = int(time.time())
        
        # 2. Криптографически стойкая энтропия (32 байта)
        entropy = os.urandom(32)
        
        # 3. Подписываем первые 40 байт (timestamp + entropy)
        header = struct.pack(">Q", timestamp) + entropy
        signed = self.signing_key.sign(header)
        signature = signed.signature  # 64 байта
        
        return SignalPacket(timestamp, entropy, signature)
    
    def broadcast(self) -> SignalPacket:
        """Генерирует и публикует сигнал"""
        
        packet = self.generate_packet()
        
        # Сохраняем latest.bin (104 байта для Rust клиентов)
        bin_path = self.output_dir / "latest.bin"
        with open(bin_path, 'wb') as f:
            f.write(packet.to_bytes())
        
        # Сохраняем latest.json (для отладки и веб-клиентов)
        json_path = self.output_dir / "latest.json"
        with open(json_path, 'w') as f:
            json.dump(packet.to_dict(), f, indent=2)
        
        # Архивируем по timestamp (для Grace Period)
        archive_path = self.output_dir / f"sigma_{packet.timestamp}.bin"
        with open(archive_path, 'wb') as f:
            f.write(packet.to_bytes())
        
        print(f"[ONTO] σ(t) broadcasted: {packet.entropy[:8].hex()}... | ts: {packet.timestamp}")
        
        return packet
    
    def run_forever(self, interval_seconds: int = 300):
        """Запускает бесконечный цикл вещания"""
        print(f"[ONTO] Entropy Streamer started. Interval: {interval_seconds}s")
        print(f"[ONTO] Output: {self.output_dir.absolute()}")
        print(f"[ONTO] Packet size: 104 bytes (8 ts + 32 entropy + 64 sig)")
        
        while True:
            try:
                self.broadcast()
                
                # Очистка старых архивов (>48 часов)
                self._cleanup_old_signals(max_age_hours=48)
                
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                print("\n[ONTO] Streamer stopped")
                break
            except Exception as e:
                print(f"[ONTO] Error: {e}")
                time.sleep(10)
    
    def _cleanup_old_signals(self, max_age_hours: int = 48):
        """Удаляет старые архивные сигналы"""
        cutoff = time.time() - (max_age_hours * 3600)
        
        for file in self.output_dir.glob("sigma_*.bin"):
            try:
                ts = int(file.stem.split("_")[1])
                if ts < cutoff:
                    file.unlink()
                    print(f"[ONTO] Cleaned up: {file.name}")
            except (ValueError, IndexError):
                pass


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ONTO Entropy Streamer')
    parser.add_argument('--interval', type=int, default=300, help='Broadcast interval in seconds')
    parser.add_argument('--output', type=str, default='./signal', help='Output directory')
    parser.add_argument('--once', action='store_true', help='Broadcast once and exit')
    
    args = parser.parse_args()
    
    streamer = EntropyStreamer(output_dir=args.output)
    
    if args.once:
        packet = streamer.broadcast()
        print(json.dumps(packet.to_dict(), indent=2))
    else:
        streamer.run_forever(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
