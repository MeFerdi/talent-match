import pytest
import json
from pathlib import Path
from integrations.openai import OpenAIClient, ExtensionEvaluation

def load_test_cases():
    """Load test cases from sample files"""
    test_data_dir = Path(__file__).parent.parent / "test_data"
    
    # Load from text file
    text_cases = []
    with open(test_data_dir / "sample_requests.txt") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split("|")
                text_cases.append({
                    "input": parts[0],
                    "expected_approved": parts[1] == "True",
                    "expected_confidence": float(parts[2]),
                    "expected_reason": parts[3]
                })
    
    # Load from JSON file
    with open(test_data_dir / "sample_responses.json") as f:
        json_cases = json.load(f)
    
    return {
        "text_cases": text_cases,
        "valid_json_cases": json_cases["valid_responses"],
        "invalid_json_cases": json_cases["invalid_responses"]
    }

@pytest.fixture
def test_cases():
    return load_test_cases()

@pytest.fixture
def openai_client():
    return OpenAIClient()

def test_text_cases(openai_client, test_cases):
    """Test using the text file format cases"""
    for case in test_cases["text_cases"]:
        # Mock the API call or use real implementation
        result = openai_client.evaluate_extension(case["input"])
        
        if case["expected_approved"]:
            assert result is not None
            assert result.approved == case["expected_approved"]
            assert result.confidence == pytest.approx(case["expected_confidence"])
            assert case["expected_reason"] in result.reason
        else:
            assert result is None or not result.approved

def test_json_cases(openai_client, test_cases):
    """Test using the JSON format cases"""
    for case in test_cases["valid_json_cases"]:
        result = openai_client.evaluate_extension(case["input"])
        assert result == ExtensionEvaluation(**case["output"])
    
    for case in test_cases["invalid_json_cases"]:
        result = openai_client.evaluate_extension(case["input"])
        assert result is None