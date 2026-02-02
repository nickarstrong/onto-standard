//! Poisoned Metrics - "отравленная" математика
//!
//! Все метрики вычисляются с учётом σ(t) дрейфа.
//! Без актуального сигнала результаты невалидны на сервере-нотариусе.

use crate::entropy::EntropyState;
use crate::{EvaluationTask, EvaluationResult};

/// Базовые пороги (из onto-standard)
const U_RECALL_THRESHOLD: f32 = 0.75;
const ECE_THRESHOLD: f32 = 0.10;
const RISK_SCORE_BASE: f32 = 50.0;

#[derive(Clone)]
pub struct PoisonedMetrics {
    // Можно добавить кэширование и настройки
}

impl PoisonedMetrics {
    pub fn new() -> Self {
        Self {}
    }
    
    /// Главная функция оценки
    pub fn evaluate(&self, task: &EvaluationTask, entropy: &EntropyState) -> EvaluationResult {
        // Вычисляем базовые метрики
        let raw_u_recall = self.calculate_u_recall_raw(&task.predictions, &task.uncertainties);
        let raw_ece = self.calculate_ece_raw(&task.predictions, &task.uncertainties);
        
        // Применяем "отравление" через σ(t)
        let u_recall_drift = entropy.compute_drift(b"u_recall_salt_v1");
        let ece_drift = entropy.compute_drift(b"ece_salt_v1");
        
        // Финальные "отравленные" значения
        let u_recall = (raw_u_recall + u_recall_drift).clamp(0.0, 1.0);
        let ece = (raw_ece + ece_drift).clamp(0.0, 1.0);
        
        // Risk Score - комбинированная метрика
        let risk_score = self.calculate_risk_score(u_recall, ece);
        
        // Proof hash для манифеста
        let proof_data = format!("{}:{}:{}:{}", 
            task.model_id, u_recall, ece, risk_score
        );
        let proof_hash = entropy.compute_proof(proof_data.as_bytes());
        
        // Определяем статус
        let status = if entropy.is_sandbox() {
            "SANDBOX_MODE"
        } else if u_recall >= U_RECALL_THRESHOLD && ece <= ECE_THRESHOLD {
            "COMPLIANT"
        } else {
            "NON_COMPLIANT"
        };
        
        EvaluationResult {
            model_id: task.model_id.clone(),
            u_recall,
            ece,
            risk_score,
            sigma_id: entropy.get_sigma_id(),
            proof_hash,
            status: status.to_string(),
        }
    }
    
    /// U-Recall: способность модели "знать, что она не знает"
    /// 
    /// Формула: доля случаев, где высокая неопределённость коррелирует
    /// с низкой точностью предсказания.
    fn calculate_u_recall_raw(&self, predictions: &[f32], uncertainties: &[f32]) -> f32 {
        if predictions.is_empty() || uncertainties.is_empty() {
            return 0.0;
        }
        
        let n = predictions.len().min(uncertainties.len());
        if n == 0 {
            return 0.0;
        }
        
        // Простая эвристика: считаем сколько раз высокая неопределённость
        // соответствует "проблемному" предсказанию (близко к 0.5)
        let mut correct_uncertain = 0;
        let mut total_uncertain = 0;
        
        for i in 0..n {
            let pred = predictions[i];
            let uncert = uncertainties[i];
            
            // Высокая неопределённость (> 0.3)
            if uncert > 0.3 {
                total_uncertain += 1;
                
                // Предсказание неуверенное (близко к 0.5)
                if (pred - 0.5).abs() < 0.2 {
                    correct_uncertain += 1;
                }
            }
        }
        
        if total_uncertain == 0 {
            return 0.8;  // Нет неопределённых случаев - хороший знак
        }
        
        correct_uncertain as f32 / total_uncertain as f32
    }
    
    /// ECE: Expected Calibration Error
    /// 
    /// Насколько уверенность модели соответствует реальной точности.
    fn calculate_ece_raw(&self, predictions: &[f32], uncertainties: &[f32]) -> f32 {
        if predictions.is_empty() || uncertainties.is_empty() {
            return 0.5;  // Максимальная ошибка при отсутствии данных
        }
        
        let n = predictions.len().min(uncertainties.len());
        if n == 0 {
            return 0.5;
        }
        
        // Упрощённый ECE: средняя разница между уверенностью и "точностью"
        let mut total_error = 0.0;
        
        for i in 0..n {
            let confidence = 1.0 - uncertainties[i];  // Уверенность = 1 - неопределённость
            let accuracy_proxy = (predictions[i] - 0.5).abs() * 2.0;  // Proxy для точности
            
            total_error += (confidence - accuracy_proxy).abs();
        }
        
        total_error / n as f32
    }
    
    /// Risk Score: 0-100, где ниже = лучше
    fn calculate_risk_score(&self, u_recall: f32, ece: f32) -> f32 {
        // Формула: базовый риск минус бонусы за хорошие метрики
        let u_recall_factor = (1.0 - u_recall) * 30.0;  // До 30 пунктов риска
        let ece_factor = ece * 20.0;  // До 20 пунктов риска
        
        let score = RISK_SCORE_BASE - (u_recall * 25.0) + u_recall_factor + ece_factor;
        
        score.clamp(0.0, 100.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_u_recall_calculation() {
        let metrics = PoisonedMetrics::new();
        
        // Идеальный случай: высокая неопределённость при неуверенных предсказаниях
        let predictions = vec![0.5, 0.5, 0.5, 0.9, 0.1];
        let uncertainties = vec![0.8, 0.7, 0.6, 0.1, 0.1];
        
        let u_recall = metrics.calculate_u_recall_raw(&predictions, &uncertainties);
        assert!(u_recall > 0.5, "U-Recall should be good: {}", u_recall);
    }
    
    #[test]
    fn test_poisoned_evaluation() {
        let metrics = PoisonedMetrics::new();
        let mut entropy = EntropyState::new();
        
        // Обновляем sigma
        entropy.update(&[42u8; 32], 12345);
        
        let task = EvaluationTask {
            model_id: "test_model".to_string(),
            predictions: vec![0.8, 0.2, 0.6, 0.4],
            uncertainties: vec![0.1, 0.1, 0.5, 0.5],
            timestamp: 0,
        };
        
        let result = metrics.evaluate(&task, &entropy);
        
        assert!(!result.sigma_id.is_empty());
        assert!(!result.proof_hash.is_empty());
        assert!(result.u_recall >= 0.0 && result.u_recall <= 1.0);
        assert!(result.ece >= 0.0 && result.ece <= 1.0);
        assert!(result.risk_score >= 0.0 && result.risk_score <= 100.0);
    }
    
    #[test]
    fn test_drift_affects_result() {
        let metrics = PoisonedMetrics::new();
        
        let task = EvaluationTask {
            model_id: "test".to_string(),
            predictions: vec![0.5; 10],
            uncertainties: vec![0.5; 10],
            timestamp: 0,
        };
        
        // Разные sigma должны давать разные результаты
        let mut entropy1 = EntropyState::new();
        let mut entropy2 = EntropyState::new();
        
        entropy1.update(&[1u8; 32], 100);
        entropy2.update(&[2u8; 32], 200);
        
        let result1 = metrics.evaluate(&task, &entropy1);
        let result2 = metrics.evaluate(&task, &entropy2);
        
        // U-Recall должен отличаться из-за разного drift
        assert_ne!(result1.u_recall, result2.u_recall, 
                   "Different sigma should produce different results");
    }
}
