from integrations.openai import OpenAIClient
from pathlib import Path
import json

def calculate_accuracy():
    client = OpenAIClient()
    test_data = json.loads((Path(__file__).parent / "../test_data/sample_responses.json").read_text())
    
    correct = 0
    total = 0
    
    for case in test_data["valid_responses"] + test_data["invalid_responses"]:
        result = client.evaluate_extension(case["input"])
        expected = case["output"]
        
        if expected is None:
            if result is None:
                correct += 1
        else:
            if result and all(
                getattr(result, k) == v 
                for k, v in expected.items()
            ):
                correct += 1
        
        total += 1
    
    print(f"Accuracy: {correct/total:.2%} ({correct}/{total} correct)")

if __name__ == "__main__":
    calculate_accuracy()