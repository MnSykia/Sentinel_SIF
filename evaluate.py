"""CLI entry point for the SentinelSIF held-out evaluation."""
from pathlib import Path

from evaluation import evaluate_classifier


def run_evaluation():
    result = evaluate_classifier(Path(__file__).parent)
    print("SentinelSIF held-out evaluation")
    print(f"Status: {result['status']}")
    print(f"Dataset: {result['evaluation_dataset']}")
    print(f"Test-set size: {result['test_set_size']}")
    for name, value in result["measured"].items():
        display = "Not evaluated" if value is None else f"{value * 100:.1f}%"
        print(f"{name}: {display}")
    return result


if __name__ == "__main__":
    run_evaluation()
