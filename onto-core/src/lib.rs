//! ONTO Core - Stealth Compliance SDK
//! 
//! Rust-ядро с "отравленной" математикой, зависящей от внешнего σ(t) сигнала.
//! Без актуального сигнала результаты невалидны.

use pyo3::prelude::*;
use crossbeam_channel::{unbounded, Sender, Receiver};
use std::sync::{Arc, Mutex, Once};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH, Duration};

mod entropy;
mod metrics;
mod merkle;

use entropy::EntropyState;
use metrics::PoisonedMetrics;
use merkle::MerkleBatcher;

/// Глобальное состояние (Singleton)
static INIT: Once = Once::new();
static mut VALIDATOR: Option<Arc<Mutex<OntoValidator>>> = None;

/// Задача на оценку
#[derive(Debug, Clone)]
pub struct EvaluationTask {
    pub model_id: String,
    pub predictions: Vec<f32>,
    pub uncertainties: Vec<f32>,
    pub timestamp: u64,
}

/// Результат оценки (с "отравлением")
#[derive(Debug, Clone)]
#[pyclass]
pub struct EvaluationResult {
    #[pyo3(get)]
    pub model_id: String,
    #[pyo3(get)]
    pub u_recall: f32,
    #[pyo3(get)]
    pub ece: f32,
    #[pyo3(get)]
    pub risk_score: f32,
    #[pyo3(get)]
    pub sigma_id: String,
    #[pyo3(get)]
    pub proof_hash: String,
    #[pyo3(get)]
    pub status: String,
}

/// Основной валидатор
pub struct OntoValidator {
    entropy: EntropyState,
    metrics: PoisonedMetrics,
    batcher: MerkleBatcher,
    sender: Sender<EvaluationTask>,
    signal_url: String,
    last_sync: u64,
}

impl OntoValidator {
    pub fn new(signal_url: &str) -> Self {
        let (sender, receiver) = unbounded();
        
        let mut validator = Self {
            entropy: EntropyState::new(),
            metrics: PoisonedMetrics::new(),
            batcher: MerkleBatcher::new(1000),
            sender,
            signal_url: signal_url.to_string(),
            last_sync: 0,
        };
        
        // Первичная синхронизация
        if let Err(e) = validator.sync_signal() {
            eprintln!("[ONTO] Warning: Initial sync failed: {}", e);
        }
        
        // Запускаем Stealth Worker
        validator.start_worker(receiver);
        
        validator
    }
    
    /// Синхронизация с сервером σ(t) - загрузка 104-байтного пакета
    pub fn sync_signal(&mut self) -> Result<(), String> {
        let url = format!("{}/signal/latest.bin", self.signal_url);
        
        let response = reqwest::blocking::get(&url)
            .map_err(|e| format!("Network error: {}", e))?;
        
        if !response.status().is_success() {
            return Err(format!("HTTP error: {}", response.status()));
        }
        
        let bytes = response.bytes()
            .map_err(|e| format!("Read error: {}", e))?;
        
        if bytes.len() != 104 {
            return Err(format!("Invalid packet size: {} (expected 104)", bytes.len()));
        }
        
        // Обновляем entropy state из бинарного пакета
        self.entropy.update_from_bytes(&bytes)?;
        
        self.last_sync = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        println!("[ONTO] Synced σ(t): {} | packet: 104 bytes", 
                 self.entropy.get_sigma_id());
        
        Ok(())
    }
    
    /// Запуск фонового воркера (Stealth Mode)
    fn start_worker(&self, receiver: Receiver<EvaluationTask>) {
        let entropy = self.entropy.clone();
        let metrics = self.metrics.clone();
        
        thread::Builder::new()
            .name("onto-stealth".into())
            .spawn(move || {
                println!("[ONTO] Stealth Worker started");
                
                while let Ok(task) = receiver.recv() {
                    // Вычисляем "отравленные" метрики
                    let result = metrics.evaluate(&task, &entropy);
                    
                    // TODO: Добавляем в Merkle batch
                    // batcher.add(result);
                    
                    println!("[ONTO] Evaluated: model={}, u_recall={:.4}, status={}", 
                             result.model_id, result.u_recall, result.status);
                }
            })
            .expect("Failed to spawn worker thread");
    }
    
    /// Отправка задачи на оценку (Zero Latency)
    pub fn push(&self, task: EvaluationTask) -> Result<(), String> {
        self.sender.send(task)
            .map_err(|e| format!("Channel error: {}", e))
    }
    
    /// Немедленная синхронная оценка
    pub fn evaluate_sync(&self, task: &EvaluationTask) -> EvaluationResult {
        self.metrics.evaluate(task, &self.entropy)
    }
    
    /// Проверка актуальности сигнала
    pub fn is_signal_valid(&self) -> bool {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        // Сигнал валиден 1 час (Grace Period)
        now - self.last_sync < 3600
    }
}

// ============ Python Bindings ============

#[pyfunction]
fn init(signal_url: Option<String>) -> PyResult<()> {
    let url = signal_url.unwrap_or_else(|| "http://localhost:8081".to_string());
    
    INIT.call_once(|| {
        let validator = OntoValidator::new(&url);
        unsafe {
            VALIDATOR = Some(Arc::new(Mutex::new(validator)));
        }
        println!("[ONTO] Initialized with signal URL: {}", url);
    });
    
    Ok(())
}

#[pyfunction]
fn sync() -> PyResult<()> {
    unsafe {
        if let Some(ref v) = VALIDATOR {
            let mut validator = v.lock().unwrap();
            validator.sync_signal()
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))?;
        }
    }
    Ok(())
}

#[pyfunction]
fn push(model_id: String, predictions: Vec<f32>, uncertainties: Vec<f32>) -> PyResult<()> {
    let task = EvaluationTask {
        model_id,
        predictions,
        uncertainties,
        timestamp: SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs(),
    };
    
    unsafe {
        if let Some(ref v) = VALIDATOR {
            let validator = v.lock().unwrap();
            validator.push(task)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))?;
        } else {
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "ONTO not initialized. Call onto_core.init() first"
            ));
        }
    }
    
    Ok(())
}

#[pyfunction]
fn evaluate(model_id: String, predictions: Vec<f32>, uncertainties: Vec<f32>) -> PyResult<EvaluationResult> {
    let task = EvaluationTask {
        model_id,
        predictions,
        uncertainties,
        timestamp: SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs(),
    };
    
    unsafe {
        if let Some(ref v) = VALIDATOR {
            let validator = v.lock().unwrap();
            Ok(validator.evaluate_sync(&task))
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "ONTO not initialized. Call onto_core.init() first"
            ))
        }
    }
}

#[pyfunction]
fn status() -> PyResult<String> {
    unsafe {
        if let Some(ref v) = VALIDATOR {
            let validator = v.lock().unwrap();
            let valid = validator.is_signal_valid();
            Ok(format!("Signal valid: {}, Last sync: {}s ago", 
                      valid, 
                      SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs() - validator.last_sync))
        } else {
            Ok("Not initialized".to_string())
        }
    }
}

/// Python модуль
#[pymodule]
fn onto_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(init, m)?)?;
    m.add_function(wrap_pyfunction!(sync, m)?)?;
    m.add_function(wrap_pyfunction!(push, m)?)?;
    m.add_function(wrap_pyfunction!(evaluate, m)?)?;
    m.add_function(wrap_pyfunction!(status, m)?)?;
    m.add_class::<EvaluationResult>()?;
    Ok(())
}
