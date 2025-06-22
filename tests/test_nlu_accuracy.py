#!/usr/bin/env python3
"""
Simple NLU accuracy tester for RasaMedical
Run with: python test_nlu_accuracy.py
"""

import subprocess
import sys
import os
import json
from pathlib import Path


def test_nlu_accuracy():
    """Test NLU accuracy using Rasa's built-in test command"""
    print("🧪 Testing NLU Accuracy...")
    print("=" * 50)

    # Check if we have a trained model
    models_dir = Path("models")
    if not models_dir.exists() or not list(models_dir.glob("*.tar.gz")):
        print("❌ No trained model found!")
        print("💡 Train a model first with: rasa train")
        return False

    # Get the latest model
    model_files = list(models_dir.glob("*.tar.gz"))
    latest_model = max(model_files, key=os.path.getctime)
    print(f"📦 Using model: {latest_model.name}")

    # Run NLU test
    print("\n🏃 Running NLU accuracy test...")
    print("-" * 30)

    try:
        # Test against training data (cross-validation)
        result = subprocess.run([
            sys.executable, "-m", "rasa", "test", "nlu",
            "--model", str(latest_model),
            "--nlu", "data/nlu.yml",
            "--cross-validation",
            "--folds", "3",
            "--out", "results"
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout

        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print("\n✅ NLU test completed!")

            # Try to read results
            results_file = Path("results/intent_report.json")
            if results_file.exists():
                with open(results_file, 'r') as f:
                    report = json.load(f)

                print("\n📊 **NLU ACCURACY RESULTS:**")
                print("=" * 40)

                # Overall accuracy
                if 'weighted avg' in report:
                    weighted_avg = report['weighted avg']
                    print(f"🎯 Overall Accuracy: {weighted_avg.get('f1-score', 'N/A'):.2%}")
                    print(f"📈 Precision: {weighted_avg.get('precision', 'N/A'):.2%}")
                    print(f"📈 Recall: {weighted_avg.get('recall', 'N/A'):.2%}")

                # Per-intent breakdown
                print("\n🔍 **Per-Intent Performance:**")
                print("-" * 30)
                for intent, metrics in report.items():
                    if intent not in ['accuracy', 'macro avg', 'weighted avg'] and isinstance(metrics, dict):
                        f1 = metrics.get('f1-score', 0)
                        support = metrics.get('support', 0)
                        print(f"{intent:25} | F1: {f1:.2%} | Examples: {support}")

                return True
            else:
                print("⚠️  Results file not found, but test completed")
                return True

        else:
            print(f"\n❌ NLU test failed (exit code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print("⏰ Test timed out (took longer than 5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running NLU test: {e}")
        return False


def quick_intent_test():
    """Quick manual test of specific intents"""
    print("\n🚀 **Quick Intent Test:**")
    print("=" * 30)

    test_phrases = [
        "I want to book an appointment",
        "Show me all doctors",
        "I have chest pain",
        "What are your working hours?",
        "Cancel my appointment",
        "I need to see a pediatric cardiologist"
    ]

    for phrase in test_phrases:
        try:
            result = subprocess.run([
                sys.executable, "-m", "rasa", "shell", "nlu",
                "--quiet"
            ], input=phrase, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Parse the output to extract intent
                output = result.stdout
                if "intent" in output:
                    print(f"'{phrase}' -> {output.strip()}")
                else:
                    print(f"'{phrase}' -> Could not parse result")
            else:
                print(f"'{phrase}' -> Error testing")

        except Exception as e:
            print(f"'{phrase}' -> Error: {e}")


if __name__ == "__main__":
    print("🎯 NLU Accuracy Tester")
    print("Choose an option:")
    print("1. Full accuracy test (recommended)")
    print("2. Quick intent test")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        success = test_nlu_accuracy()
        sys.exit(0 if success else 1)
    elif choice == "2":
        quick_intent_test()
    else:
        print("Invalid choice!")
        sys.exit(1)
