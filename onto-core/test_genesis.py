#!/usr/bin/env python3
"""
ONTO Genesis - Integration Test
Проверяет всю цепочку: Signal → Core → Evaluation
"""

import time
import json
import subprocess
import sys
from pathlib import Path

def test_signal_server():
    """Проверка Signal Server"""
    print("\n=== Testing Signal Server ===")
    
    try:
        import requests
        
        # Статус
        r = requests.get("http://localhost:8081/signal/status", timeout=5)
        if r.status_code == 200:
            print(f"✓ Status: {r.json()}")
        else:
            print(f"✗ Status failed: {r.status_code}")
            return False
        
        # Latest signal
        r = requests.get("http://localhost:8081/signal/latest.json", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"✓ Latest σ(t): sigma_id={data['sigma_id']}, entropy={data['entropy_hash']}")
        else:
            print(f"✗ Latest signal failed: {r.status_code}")
            return False
        
        # Verify key
        r = requests.get("http://localhost:8081/signal/verify-key", timeout=5)
        if r.status_code == 200:
            print(f"✓ Verify key available")
        else:
            print(f"✗ Verify key failed: {r.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ Signal server not running. Start with:")
        print("  cd onto-signal && python server.py")
        return False
    except ImportError:
        print("✗ requests not installed: pip install requests")
        return False


def test_onto_core():
    """Проверка ONTO Core"""
    print("\n=== Testing ONTO Core ===")
    
    try:
        import onto_core
        
        # Init
        print("Initializing...")
        onto_core.init("http://localhost:8081")
        print("✓ Initialized")
        
        # Status
        status = onto_core.status()
        print(f"✓ Status: {status}")
        
        # Sync
        print("Syncing signal...")
        onto_core.sync()
        print("✓ Signal synced")
        
        # Evaluate
        print("Running evaluation...")
        result = onto_core.evaluate(
            model_id="test_model_v1",
            predictions=[0.8, 0.2, 0.6, 0.4, 0.9, 0.1],
            uncertainties=[0.1, 0.1, 0.5, 0.5, 0.05, 0.05]
        )
        
        print(f"✓ Evaluation complete:")
        print(f"  - U-Recall: {result.u_recall:.4f}")
        print(f"  - ECE: {result.ece:.4f}")
        print(f"  - Risk Score: {result.risk_score:.1f}")
        print(f"  - Sigma ID: {result.sigma_id}")
        print(f"  - Proof Hash: {result.proof_hash}")
        print(f"  - Status: {result.status}")
        
        # Push (async)
        print("Testing async push...")
        onto_core.push(
            model_id="test_model_v1",
            predictions=[0.7],
            uncertainties=[0.2]
        )
        print("✓ Async push successful")
        
        return True
        
    except ImportError:
        print("✗ onto_core not installed. Build with:")
        print("  cd onto-core && maturin develop")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_drift_consistency():
    """Проверка детерминизма drift"""
    print("\n=== Testing Drift Consistency ===")
    
    try:
        import onto_core
        
        onto_core.init("http://localhost:8081")
        
        # Одинаковые входы должны давать одинаковые результаты
        result1 = onto_core.evaluate("model_a", [0.5, 0.5], [0.3, 0.3])
        result2 = onto_core.evaluate("model_a", [0.5, 0.5], [0.3, 0.3])
        
        if result1.u_recall == result2.u_recall:
            print("✓ Drift is deterministic")
        else:
            print(f"✗ Drift not deterministic: {result1.u_recall} vs {result2.u_recall}")
            return False
        
        # Разные модели должны давать разные proof_hash
        result_a = onto_core.evaluate("model_a", [0.5], [0.3])
        result_b = onto_core.evaluate("model_b", [0.5], [0.3])
        
        if result_a.proof_hash != result_b.proof_hash:
            print("✓ Different models have different proofs")
        else:
            print("✗ Proof hash collision detected!")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("=" * 50)
    print("ONTO Genesis - Integration Test Suite")
    print("=" * 50)
    
    results = []
    
    # Test 1: Signal Server
    results.append(("Signal Server", test_signal_server()))
    
    # Test 2: ONTO Core
    results.append(("ONTO Core", test_onto_core()))
    
    # Test 3: Drift Consistency
    results.append(("Drift Consistency", test_drift_consistency()))
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All tests passed! ONTO Genesis is operational.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
