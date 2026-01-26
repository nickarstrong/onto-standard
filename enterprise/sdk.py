"""
ONTO Enterprise Python SDK

Usage:
    from onto_enterprise import ONTOClient
    
    client = ONTOClient(api_key="onto_xxx...")
    
    # Submit evaluation
    result = client.evaluate(
        model_name="My Model",
        organization="My Company",
        predictions=[
            {"id": "q1", "label": "KNOWN", "confidence": 0.9},
            {"id": "q2", "label": "UNKNOWN", "confidence": 0.7},
        ]
    )
    
    # Check status
    status = client.status(result["evaluation_id"])
    
    # Get report
    report = client.report(result["evaluation_id"])
"""

import time
from typing import List, Dict, Optional
import requests


class ONTOClient:
    """ONTO Enterprise API Client"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.onto-bench.org",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers["X-API-Key"] = api_key
        self.session.headers["Content-Type"] = "application/json"
    
    def _request(self, method: str, path: str, **kwargs) -> Dict:
        """Make API request"""
        url = f"{self.base_url}{path}"
        response = self.session.request(method, url, **kwargs)
        
        if response.status_code == 401:
            raise ONTOAuthError("Invalid API key")
        elif response.status_code == 403:
            raise ONTOPermissionError(response.json().get("detail", "Permission denied"))
        elif response.status_code == 404:
            raise ONTONotFoundError("Resource not found")
        elif response.status_code >= 400:
            raise ONTOAPIError(f"API error: {response.text}")
        
        return response.json()
    
    def evaluate(
        self,
        model_name: str,
        organization: str,
        predictions: List[Dict],
        contact_email: str = None,
        model_version: str = None,
        notes: str = None,
        wait: bool = False,
        poll_interval: int = 5,
        timeout: int = 300,
    ) -> Dict:
        """
        Submit model for evaluation
        
        Args:
            model_name: Name of the model
            organization: Your organization name
            predictions: List of predictions, each with id, label, confidence
            contact_email: Contact email for report
            model_version: Optional model version string
            notes: Optional notes about the evaluation
            wait: If True, wait for evaluation to complete
            poll_interval: Seconds between status checks (if wait=True)
            timeout: Maximum seconds to wait (if wait=True)
        
        Returns:
            Evaluation result with evaluation_id
        """
        payload = {
            "model_name": model_name,
            "organization": organization,
            "predictions": predictions,
            "contact_email": contact_email or "noreply@example.com",
            "model_version": model_version,
            "notes": notes,
        }
        
        result = self._request("POST", "/enterprise/evaluate", json=payload)
        
        if wait:
            result = self._wait_for_completion(
                result["evaluation_id"],
                poll_interval,
                timeout,
            )
        
        return result
    
    def status(self, evaluation_id: str) -> Dict:
        """
        Get evaluation status
        
        Args:
            evaluation_id: ID of the evaluation
        
        Returns:
            Evaluation status and metrics (if completed)
        """
        return self._request("GET", f"/enterprise/status/{evaluation_id}")
    
    def report(self, evaluation_id: str, output_path: str = None) -> str:
        """
        Get evaluation report
        
        Args:
            evaluation_id: ID of the evaluation
            output_path: Optional path to save report HTML
        
        Returns:
            Report HTML content
        """
        url = f"{self.base_url}/enterprise/report/{evaluation_id}"
        response = self.session.get(url)
        
        if response.status_code != 200:
            raise ONTOAPIError(f"Failed to get report: {response.text}")
        
        content = response.text
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(content)
        
        return content
    
    def list_evaluations(self) -> List[Dict]:
        """
        List all evaluations
        
        Returns:
            List of evaluation summaries
        """
        return self._request("GET", "/enterprise/evaluations")
    
    def _wait_for_completion(
        self,
        evaluation_id: str,
        poll_interval: int,
        timeout: int,
    ) -> Dict:
        """Wait for evaluation to complete"""
        start = time.time()
        
        while time.time() - start < timeout:
            result = self.status(evaluation_id)
            
            if result["status"] == "completed":
                return result
            elif result["status"] == "failed":
                raise ONTOEvaluationError(f"Evaluation failed: {result.get('error')}")
            
            time.sleep(poll_interval)
        
        raise ONTOTimeoutError(f"Evaluation did not complete within {timeout} seconds")


# Exceptions

class ONTOError(Exception):
    """Base ONTO error"""
    pass

class ONTOAuthError(ONTOError):
    """Authentication error"""
    pass

class ONTOPermissionError(ONTOError):
    """Permission denied"""
    pass

class ONTONotFoundError(ONTOError):
    """Resource not found"""
    pass

class ONTOAPIError(ONTOError):
    """API error"""
    pass

class ONTOEvaluationError(ONTOError):
    """Evaluation failed"""
    pass

class ONTOTimeoutError(ONTOError):
    """Timeout waiting for completion"""
    pass


# Convenience functions

def quick_evaluate(
    api_key: str,
    model_name: str,
    predictions_file: str,
    organization: str = "Unknown",
) -> Dict:
    """
    Quick evaluation from JSONL file
    
    Args:
        api_key: ONTO API key
        model_name: Name of your model
        predictions_file: Path to JSONL file with predictions
        organization: Your organization name
    
    Returns:
        Evaluation result with metrics
    """
    import json
    
    predictions = []
    with open(predictions_file) as f:
        for line in f:
            predictions.append(json.loads(line))
    
    client = ONTOClient(api_key)
    return client.evaluate(
        model_name=model_name,
        organization=organization,
        predictions=predictions,
        wait=True,
    )


# CLI

if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 4:
        print("Usage: python sdk.py <api_key> <model_name> <predictions.jsonl>")
        sys.exit(1)
    
    api_key = sys.argv[1]
    model_name = sys.argv[2]
    predictions_file = sys.argv[3]
    
    print(f"Evaluating {model_name}...")
    
    result = quick_evaluate(api_key, model_name, predictions_file)
    
    print(f"\nEvaluation complete!")
    print(f"Risk Score: {result.get('risk_score', 'N/A')}")
    print(f"Unknown Detection: {result.get('metrics', {}).get('unknown_detection', {}).get('recall', 'N/A'):.1%}")
    print(f"ECE: {result.get('metrics', {}).get('calibration', {}).get('ece', 'N/A'):.3f}")
    print(f"\nFull result:")
    print(json.dumps(result, indent=2))
