"""
ONTO Bridge — Адаптер между app.py и onto_core (Rust)

Задача: app.py делает лингвистический анализ текста (regex факторы),
onto_core делает математику (ECE, U-Recall, poisoned scoring, HMAC proof).

Bridge конвертирует лингвистические сигналы → predictions/uncertainties → onto_core.

Fallback: если onto_core не доступен (сборка, sandbox) — использует Python-реализацию
тех же формул что в Rust, но без poisoning (→ SANDBOX_MODE).
"""

import hashlib
import hmac
import struct
import time
import math
from typing import Optional

# ============ Попытка импорта Rust-ядра ============

_RUST_AVAILABLE = False
_onto_core = None

try:
    import onto_core as _onto_core
    _RUST_AVAILABLE = True
except ImportError:
    pass


# ============ Python Fallback (зеркало metrics.rs) ============

class PythonFallbackEngine:
    """
    Зеркало onto_core Rust логики на Python.
    Используется когда .pyd/.so не доступен.
    Результаты в SANDBOX_MODE (без σ(t) poisoning).
    """
    
    U_RECALL_THRESHOLD = 0.75
    ECE_THRESHOLD = 0.10
    RISK_SCORE_BASE = 50.0
    
    def evaluate(self, model_id: str, predictions: list, uncertainties: list) -> dict:
        """Зеркало PoisonedMetrics::evaluate() из metrics.rs, без poisoning."""
        
        raw_u_recall = self._calculate_u_recall(predictions, uncertainties)
        raw_ece = self._calculate_ece(predictions, uncertainties)
        risk_score = self._calculate_risk_score(raw_u_recall, raw_ece)
        
        # Без σ(t) — результат не "отравлен"
        # Proof = SHA256 вместо HMAC (нет entropy ключа)
        proof_data = f"{model_id}:{raw_u_recall}:{raw_ece}:{risk_score}"
        proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()[:32]
        
        # Статус
        if raw_u_recall >= self.U_RECALL_THRESHOLD and raw_ece <= self.ECE_THRESHOLD:
            status = "SANDBOX_COMPLIANT"
        else:
            status = "SANDBOX_NON_COMPLIANT"
        
        return {
            "model_id": model_id,
            "u_recall": round(raw_u_recall, 4),
            "ece": round(raw_ece, 4),
            "risk_score": round(risk_score, 2),
            "sigma_id": "σ_SANDBOX",
            "proof_hash": proof_hash,
            "status": status,
            "engine": "python_fallback",
        }
    
    def _calculate_u_recall(self, predictions: list, uncertainties: list) -> float:
        """Зеркало calculate_u_recall_raw() из metrics.rs"""
        if not predictions or not uncertainties:
            return 0.0
        
        n = min(len(predictions), len(uncertainties))
        if n == 0:
            return 0.0
        
        correct_uncertain = 0
        total_uncertain = 0
        
        for i in range(n):
            pred = predictions[i]
            uncert = uncertainties[i]
            
            if uncert > 0.3:
                total_uncertain += 1
                if abs(pred - 0.5) < 0.2:
                    correct_uncertain += 1
        
        if total_uncertain == 0:
            return 0.8
        
        return correct_uncertain / total_uncertain
    
    def _calculate_ece(self, predictions: list, uncertainties: list) -> float:
        """Зеркало calculate_ece_raw() из metrics.rs"""
        if not predictions or not uncertainties:
            return 0.5
        
        n = min(len(predictions), len(uncertainties))
        if n == 0:
            return 0.5
        
        total_error = 0.0
        for i in range(n):
            confidence = 1.0 - uncertainties[i]
            accuracy_proxy = abs(predictions[i] - 0.5) * 2.0
            total_error += abs(confidence - accuracy_proxy)
        
        return total_error / n
    
    def _calculate_risk_score(self, u_recall: float, ece: float) -> float:
        """Зеркало calculate_risk_score() из metrics.rs"""
        u_recall_factor = (1.0 - u_recall) * 30.0
        ece_factor = ece * 20.0
        score = self.RISK_SCORE_BASE - (u_recall * 25.0) + u_recall_factor + ece_factor
        return max(0.0, min(100.0, score))


# ============ Linguistic → Numerical Converter ============

class LinguisticConverter:
    """
    Конвертирует лингвистические факторы из app.py (regex-based)
    в числовые predictions/uncertainties для onto_core.
    
    Маппинг:
    - Каждый фактор → одна prediction точка
    - Вес фактора → uncertainty (инверсия)
    """
    
    # Факторы из app.py compute_risk_score() и их семантика
    FACTOR_MAP = {
        # factor_name → (is_risk_signal, base_uncertainty)
        "linguistic_uncertainty":   (True,  0.15),  # Высокое = высокий риск
        "confidence_calibration":   (True,  0.20),  # Miscalibration = риск
        "logprob_entropy":          (True,  0.25),  # Высокая энтропия = риск
        "semantic_consistency":     (False, 0.20),  # Высокое = хорошо (инверсия)
        "ground_truth_accuracy":    (False, 0.10),  # Высокое = хорошо (инверсия)
        "refusal_awareness":        (False, 0.15),  # Высокое = хорошо
        "domain_risk_adjustment":   (True,  0.30),  # Множитель
    }
    
    @classmethod
    def convert(cls, factors: dict, weights: dict) -> tuple:
        """
        Конвертация лингвистических факторов → (predictions, uncertainties)
        
        Args:
            factors: {"linguistic_uncertainty": 0.35, "confidence_calibration": 0.22, ...}
            weights: {"linguistic_uncertainty": 0.20, ...}
        
        Returns:
            (predictions: list[float], uncertainties: list[float])
        """
        predictions = []
        uncertainties = []
        
        for factor_name, factor_value in factors.items():
            # Пропускаем внутренние/служебные факторы
            if factor_name in ("domain_multiplier", "output_length", "domain"):
                continue
            if factor_value is None or (isinstance(factor_value, float) and math.isnan(factor_value)):
                continue
            
            config = cls.FACTOR_MAP.get(factor_name)
            
            if config:
                is_risk, base_uncert = config
                
                # Prediction: для risk-сигналов высокое значение = близко к 0.5 (неуверенность)
                # Для quality-сигналов: высокое = далеко от 0.5 (уверенность)
                if is_risk:
                    prediction = 0.5 + (factor_value * 0.3)  # Risk → ближе к неуверенности
                else:
                    prediction = 0.5 - (factor_value * 0.3)  # Quality → ближе к уверенности
                
                prediction = max(0.0, min(1.0, prediction))
                
                # Uncertainty: на основе веса (высокий вес = низкая неопределённость)
                weight = weights.get(factor_name, 0.15)
                uncertainty = base_uncert + (1.0 - weight) * 0.3
                uncertainty = max(0.05, min(0.95, uncertainty))
                
            else:
                # Неизвестный фактор — средние значения
                prediction = 0.5 + (factor_value * 0.2)
                prediction = max(0.0, min(1.0, prediction))
                uncertainty = 0.5
            
            predictions.append(prediction)
            uncertainties.append(uncertainty)
        
        return predictions, uncertainties


# ============ Главный Bridge ============

class OntoBridge:
    """
    Основной мост между app.py и onto_core.
    
    Использование в app.py:
    
        from onto_bridge import bridge
        
        # В /v1/evaluate endpoint:
        linguistic_result = compute_risk_score(output, confidence, ...)  # старый regex
        
        certified_result = bridge.evaluate(
            model_id=model_id,
            linguistic_factors=linguistic_result["factors"],
            linguistic_weights=linguistic_result["weights"],
        )
        
        # certified_result содержит:
        # - u_recall, ece, risk_score (из onto_core или fallback)
        # - sigma_id, proof_hash (криптопруф)
        # - status: COMPLIANT / NON_COMPLIANT / SANDBOX_*
        # - linguistic_factors (оригинальные для display)
    """
    
    def __init__(self, signal_url: str = "https://signal.ontostandard.org"):
        self.signal_url = signal_url
        self.engine = "rust" if _RUST_AVAILABLE else "python_fallback"
        self._fallback = PythonFallbackEngine()
        self._initialized = False
        
        if _RUST_AVAILABLE:
            try:
                _onto_core.init(signal_url)
                self._initialized = True
                print(f"[ONTO Bridge] Rust engine initialized, signal: {signal_url}")
            except Exception as e:
                print(f"[ONTO Bridge] Rust init failed: {e}, using Python fallback")
                self.engine = "python_fallback"
        else:
            print("[ONTO Bridge] Rust engine not available, using Python fallback")
    
    def evaluate(
        self,
        model_id: str,
        linguistic_factors: dict,
        linguistic_weights: dict,
        raw_text: Optional[str] = None,
    ) -> dict:
        """
        Главная функция оценки.
        
        1. Конвертирует linguistic factors → numerical vectors
        2. Прогоняет через onto_core (или fallback)
        3. Возвращает enriched результат
        """
        # Конвертация linguistic → numerical
        predictions, uncertainties = LinguisticConverter.convert(
            linguistic_factors, linguistic_weights
        )
        
        # Если нет данных — минимальный результат
        if not predictions:
            predictions = [0.5]
            uncertainties = [0.5]
        
        # Оценка через движок
        if self.engine == "rust" and _RUST_AVAILABLE:
            result = self._evaluate_rust(model_id, predictions, uncertainties)
        else:
            result = self._fallback.evaluate(model_id, predictions, uncertainties)
        
        # Обогащаем лингвистическими факторами
        result["linguistic_factors"] = linguistic_factors
        result["linguistic_weights"] = linguistic_weights
        result["engine"] = self.engine
        result["input_dimensions"] = len(predictions)
        
        # Layer determination (совместимость со старым API)
        result["layer"] = self._determine_layer(result)
        
        return result
    
    def _evaluate_rust(self, model_id: str, predictions: list, uncertainties: list) -> dict:
        """Оценка через Rust onto_core."""
        try:
            r = _onto_core.evaluate(model_id, predictions, uncertainties)
            return {
                "model_id": r.model_id,
                "u_recall": round(r.u_recall, 4),
                "ece": round(r.ece, 4),
                "risk_score": round(r.risk_score, 2),
                "sigma_id": r.sigma_id,
                "proof_hash": r.proof_hash,
                "status": r.status,
                "engine": "rust",
            }
        except Exception as e:
            print(f"[ONTO Bridge] Rust evaluation failed: {e}, falling back to Python")
            return self._fallback.evaluate(model_id, predictions, uncertainties)
    
    def _determine_layer(self, result: dict) -> str:
        """Определяет ONTO Layer из результата (L1/L2/L3)."""
        rs = result.get("risk_score", 50)
        
        if rs <= 25:
            return "L3"  # Full Certification
        elif rs <= 50:
            return "L2"  # Standard Evaluation
        else:
            return "L1"  # Basic Calibration
    
    def status(self) -> dict:
        """Статус движка."""
        info = {
            "engine": self.engine,
            "rust_available": _RUST_AVAILABLE,
            "initialized": self._initialized,
            "signal_url": self.signal_url,
        }
        
        if _RUST_AVAILABLE and self._initialized:
            try:
                info["signal_status"] = _onto_core.status()
            except Exception:
                info["signal_status"] = "error"
        
        return info
    
    def push_async(self, model_id: str, predictions: list, uncertainties: list):
        """Async push (Zero Latency) — только Rust."""
        if _RUST_AVAILABLE and self._initialized:
            try:
                _onto_core.push(model_id, predictions, uncertainties)
            except Exception as e:
                print(f"[ONTO Bridge] Async push failed: {e}")


# ============ Singleton ============

bridge = OntoBridge()
