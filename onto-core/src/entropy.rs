//! Entropy State - работа с σ(t) сигналом
//!
//! Этот модуль отвечает за хранение, верификацию и применение
//! динамического сигнала энтропии.
//!
//! Signal Packet: 104 bytes
//! - timestamp: 8 bytes (u64 BE)
//! - entropy: 32 bytes
//! - signature: 64 bytes (ED25519)

use hmac::{Hmac, Mac};
use sha2::Sha256;
use std::sync::{Arc, RwLock};

type HmacSha256 = Hmac<Sha256>;

/// 104-байтный пакет сигнала
#[derive(Clone, Debug)]
pub struct SignalPacket {
    pub timestamp: u64,
    pub entropy: [u8; 32],
    pub signature: [u8; 64],
}

impl SignalPacket {
    /// Парсинг из бинарного формата (104 bytes)
    pub fn from_bytes(data: &[u8]) -> Result<Self, String> {
        if data.len() != 104 {
            return Err(format!("Invalid packet size: {} (expected 104)", data.len()));
        }
        
        let timestamp = u64::from_be_bytes(data[0..8].try_into().unwrap());
        
        let mut entropy = [0u8; 32];
        entropy.copy_from_slice(&data[8..40]);
        
        let mut signature = [0u8; 64];
        signature.copy_from_slice(&data[40..104]);
        
        Ok(Self { timestamp, entropy, signature })
    }
    
    /// Сериализация в бинарный формат
    pub fn to_bytes(&self) -> [u8; 104] {
        let mut result = [0u8; 104];
        result[0..8].copy_from_slice(&self.timestamp.to_be_bytes());
        result[8..40].copy_from_slice(&self.entropy);
        result[40..104].copy_from_slice(&self.signature);
        result
    }
    
    /// Получить данные для верификации подписи (первые 40 байт)
    pub fn signable_data(&self) -> [u8; 40] {
        let mut data = [0u8; 40];
        data[0..8].copy_from_slice(&self.timestamp.to_be_bytes());
        data[8..40].copy_from_slice(&self.entropy);
        data
    }
    
    /// Sigma ID для логов
    pub fn sigma_id(&self) -> String {
        format!("σ_{}", self.timestamp)
    }
}

/// Состояние энтропии (thread-safe)
#[derive(Clone)]
pub struct EntropyState {
    inner: Arc<RwLock<EntropyInner>>,
}

struct EntropyInner {
    /// Текущий пакет
    current: Option<SignalPacket>,
    
    /// Предыдущий пакет для Grace Period
    previous: Option<SignalPacket>,
    
    /// Публичный ключ для верификации (ED25519)
    verify_key: Option<[u8; 32]>,
}

impl EntropyState {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(RwLock::new(EntropyInner {
                current: None,
                previous: None,
                verify_key: None,
            })),
        }
    }
    
    /// Обновление сигнала из бинарных данных
    pub fn update_from_bytes(&mut self, data: &[u8]) -> Result<(), String> {
        let packet = SignalPacket::from_bytes(data)?;
        
        // TODO: Верификация подписи
        // self.verify_signature(&packet)?;
        
        let mut inner = self.inner.write().unwrap();
        
        // Сохраняем предыдущий для Grace Period
        inner.previous = inner.current.take();
        inner.current = Some(packet);
        
        Ok(())
    }
    
    /// Обновление сигнала (legacy - из отдельных компонентов)
    pub fn update(&mut self, sigma: &[u8], slot_id: u64) {
        let mut inner = self.inner.write().unwrap();
        
        // Создаём пакет из компонентов
        let mut entropy = [0u8; 32];
        let len = sigma.len().min(32);
        entropy[..len].copy_from_slice(&sigma[..len]);
        
        let packet = SignalPacket {
            timestamp: slot_id,
            entropy,
            signature: [0u8; 64], // Пустая подпись для legacy
        };
        
        inner.previous = inner.current.take();
        inner.current = Some(packet);
    }
    
    /// Получить текущий sigma_id
    pub fn get_sigma_id(&self) -> String {
        let inner = self.inner.read().unwrap();
        inner.current
            .as_ref()
            .map(|p| p.sigma_id())
            .unwrap_or_else(|| "σ_SANDBOX".to_string())
    }
    
    /// Получить текущую entropy
    fn get_entropy(&self) -> [u8; 32] {
        let inner = self.inner.read().unwrap();
        inner.current
            .as_ref()
            .map(|p| p.entropy)
            .unwrap_or([0u8; 32])
    }
    
    /// Вычисляет динамический дрейф для метрики
    /// 
    /// Формула: drift = SHA256(entropy + salt) → float в диапазоне [-0.05, +0.05]
    /// 
    /// Это "отравляет" результат так, что без знания entropy
    /// невозможно получить валидное значение.
    pub fn compute_drift(&self, salt: &[u8]) -> f32 {
        let entropy = self.get_entropy();
        
        // SHA256(entropy + salt) для детерминированного drift
        use sha2::Digest;
        let mut hasher = sha2::Sha256::new();
        hasher.update(&entropy);
        hasher.update(salt);
        let result = hasher.finalize();
        
        // Берём первые 4 байта и превращаем в float [0, 1)
        let raw = u32::from_be_bytes([result[0], result[1], result[2], result[3]]);
        let normalized = raw as f32 / u32::MAX as f32;
        
        // Масштабируем до [-0.05, +0.05] (±5% дрейф)
        (normalized * 0.10) - 0.05
    }
    
    /// Вычисляет HMAC-proof для включения в манифест
    pub fn compute_proof(&self, data: &[u8]) -> String {
        let entropy = self.get_entropy();
        
        let mut mac = HmacSha256::new_from_slice(&entropy)
            .expect("HMAC accepts any key size");
        mac.update(data);
        
        let result = mac.finalize().into_bytes();
        hex::encode(&result[..16])  // 16 байт = 32 hex символа
    }
    
    /// Проверка: sandbox mode (нет сигнала или все нули)?
    pub fn is_sandbox(&self) -> bool {
        let inner = self.inner.read().unwrap();
        match &inner.current {
            None => true,
            Some(p) => p.entropy == [0u8; 32],
        }
    }
    
    /// Установить публичный ключ для верификации
    pub fn set_verify_key(&mut self, key: &[u8; 32]) {
        let mut inner = self.inner.write().unwrap();
        inner.verify_key = Some(*key);
    }
    
    /// Получить timestamp текущего сигнала
    pub fn get_timestamp(&self) -> u64 {
        let inner = self.inner.read().unwrap();
        inner.current.as_ref().map(|p| p.timestamp).unwrap_or(0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_packet_roundtrip() {
        let packet = SignalPacket {
            timestamp: 1234567890,
            entropy: [42u8; 32],
            signature: [1u8; 64],
        };
        
        let bytes = packet.to_bytes();
        assert_eq!(bytes.len(), 104);
        
        let parsed = SignalPacket::from_bytes(&bytes).unwrap();
        assert_eq!(parsed.timestamp, packet.timestamp);
        assert_eq!(parsed.entropy, packet.entropy);
        assert_eq!(parsed.signature, packet.signature);
    }
    
    #[test]
    fn test_drift_determinism() {
        let mut state = EntropyState::new();
        state.update(&[1u8; 32], 12345);
        
        let drift1 = state.compute_drift(b"u_recall");
        let drift2 = state.compute_drift(b"u_recall");
        
        assert_eq!(drift1, drift2);
    }
    
    #[test]
    fn test_drift_range() {
        let mut state = EntropyState::new();
        
        for i in 0..100 {
            let sigma: Vec<u8> = (0..32).map(|j| (i + j) as u8).collect();
            state.update(&sigma, i as u64);
            
            let drift = state.compute_drift(b"test");
            assert!(drift >= -0.05 && drift <= 0.05, "Drift out of range: {}", drift);
        }
    }
    
    #[test]
    fn test_different_salts() {
        let mut state = EntropyState::new();
        state.update(&[42u8; 32], 100);
        
        let drift_a = state.compute_drift(b"u_recall");
        let drift_b = state.compute_drift(b"ece");
        
        assert_ne!(drift_a, drift_b);
    }
}
