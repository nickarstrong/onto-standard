//! Merkle Batcher - сборка доказательств
//!
//! Собирает оценки в Merkle Tree и отправляет Root Hash
//! на сервер-нотариус для подписи.

use sha2::{Sha256, Digest};
use crate::EvaluationResult;

/// Batcher для сборки Merkle Tree
pub struct MerkleBatcher {
    /// Максимальный размер батча
    batch_limit: usize,
    
    /// Накопленные листья (хэши результатов)
    leaves: Vec<[u8; 32]>,
    
    /// URL нотариуса
    notary_url: Option<String>,
    
    /// API ключ
    api_key: Option<String>,
}

impl MerkleBatcher {
    pub fn new(batch_limit: usize) -> Self {
        Self {
            batch_limit,
            leaves: Vec::with_capacity(batch_limit),
            notary_url: None,
            api_key: None,
        }
    }
    
    /// Настройка нотариуса
    pub fn configure(&mut self, notary_url: &str, api_key: &str) {
        self.notary_url = Some(notary_url.to_string());
        self.api_key = Some(api_key.to_string());
    }
    
    /// Добавить результат оценки в батч
    pub fn add(&mut self, result: &EvaluationResult) -> Option<BatchProof> {
        // Создаём листовой хэш
        let leaf = self.hash_result(result);
        self.leaves.push(leaf);
        
        // Проверяем нужна ли финализация
        if self.leaves.len() >= self.batch_limit {
            return Some(self.finalize());
        }
        
        None
    }
    
    /// Финализация батча и отправка на подпись
    pub fn finalize(&mut self) -> BatchProof {
        let root = self.compute_merkle_root();
        let leaf_count = self.leaves.len();
        
        // Очищаем для следующего батча
        self.leaves.clear();
        
        BatchProof {
            root_hash: hex::encode(root),
            leaf_count,
            signature: None,  // Заполняется после подписи нотариусом
        }
    }
    
    /// Вычисление Merkle Root
    fn compute_merkle_root(&self) -> [u8; 32] {
        if self.leaves.is_empty() {
            return [0u8; 32];
        }
        
        if self.leaves.len() == 1 {
            return self.leaves[0];
        }
        
        let mut current_level = self.leaves.clone();
        
        // Построение дерева снизу вверх
        while current_level.len() > 1 {
            let mut next_level = Vec::new();
            
            for chunk in current_level.chunks(2) {
                let hash = if chunk.len() == 2 {
                    self.hash_pair(&chunk[0], &chunk[1])
                } else {
                    // Нечётное количество - дублируем последний
                    self.hash_pair(&chunk[0], &chunk[0])
                };
                next_level.push(hash);
            }
            
            current_level = next_level;
        }
        
        current_level[0]
    }
    
    /// Хэш пары узлов
    fn hash_pair(&self, left: &[u8; 32], right: &[u8; 32]) -> [u8; 32] {
        let mut hasher = Sha256::new();
        hasher.update(left);
        hasher.update(right);
        
        let result = hasher.finalize();
        let mut hash = [0u8; 32];
        hash.copy_from_slice(&result);
        hash
    }
    
    /// Хэш результата оценки
    fn hash_result(&self, result: &EvaluationResult) -> [u8; 32] {
        let data = format!(
            "{}:{}:{}:{}:{}:{}",
            result.model_id,
            result.u_recall,
            result.ece,
            result.risk_score,
            result.sigma_id,
            result.proof_hash
        );
        
        let mut hasher = Sha256::new();
        hasher.update(data.as_bytes());
        
        let result = hasher.finalize();
        let mut hash = [0u8; 32];
        hash.copy_from_slice(&result);
        hash
    }
    
    /// Отправка на подпись (асинхронная)
    pub fn send_to_notary(&self, proof: &mut BatchProof) -> Result<(), String> {
        let url = self.notary_url.as_ref()
            .ok_or("Notary URL not configured")?;
        let api_key = self.api_key.as_ref()
            .ok_or("API key not configured")?;
        
        let client = reqwest::blocking::Client::new();
        
        let response = client
            .post(&format!("{}/v1/sign-root", url))
            .header("X-API-KEY", api_key)
            .json(&serde_json::json!({
                "root_hash": proof.root_hash,
                "leaf_count": proof.leaf_count,
            }))
            .send()
            .map_err(|e| format!("Network error: {}", e))?;
        
        if !response.status().is_success() {
            return Err(format!("Notary error: {}", response.status()));
        }
        
        let data: serde_json::Value = response.json()
            .map_err(|e| format!("Parse error: {}", e))?;
        
        proof.signature = data["signature"].as_str().map(String::from);
        
        Ok(())
    }
    
    /// Текущий размер батча
    pub fn len(&self) -> usize {
        self.leaves.len()
    }
    
    pub fn is_empty(&self) -> bool {
        self.leaves.is_empty()
    }
}

/// Доказательство батча
#[derive(Debug, Clone)]
pub struct BatchProof {
    pub root_hash: String,
    pub leaf_count: usize,
    pub signature: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;
    
    fn make_result(id: &str) -> EvaluationResult {
        EvaluationResult {
            model_id: id.to_string(),
            u_recall: 0.85,
            ece: 0.08,
            risk_score: 25.0,
            sigma_id: "σ_12345".to_string(),
            proof_hash: "abc123".to_string(),
            status: "COMPLIANT".to_string(),
        }
    }
    
    #[test]
    fn test_merkle_root_determinism() {
        let mut batcher1 = MerkleBatcher::new(10);
        let mut batcher2 = MerkleBatcher::new(10);
        
        for i in 0..5 {
            let result = make_result(&format!("model_{}", i));
            batcher1.add(&result);
            batcher2.add(&result);
        }
        
        let proof1 = batcher1.finalize();
        let proof2 = batcher2.finalize();
        
        assert_eq!(proof1.root_hash, proof2.root_hash);
    }
    
    #[test]
    fn test_different_data_different_root() {
        let mut batcher1 = MerkleBatcher::new(10);
        let mut batcher2 = MerkleBatcher::new(10);
        
        batcher1.add(&make_result("model_a"));
        batcher2.add(&make_result("model_b"));
        
        let proof1 = batcher1.finalize();
        let proof2 = batcher2.finalize();
        
        assert_ne!(proof1.root_hash, proof2.root_hash);
    }
    
    #[test]
    fn test_auto_finalize() {
        let mut batcher = MerkleBatcher::new(3);
        
        assert!(batcher.add(&make_result("1")).is_none());
        assert!(batcher.add(&make_result("2")).is_none());
        
        // Третий должен триггерить финализацию
        let proof = batcher.add(&make_result("3"));
        assert!(proof.is_some());
        assert_eq!(proof.unwrap().leaf_count, 3);
        
        // Батч должен быть пустым
        assert!(batcher.is_empty());
    }
}
