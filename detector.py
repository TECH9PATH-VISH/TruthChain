import torch
import torch.nn.functional as F
from transformers import pipeline

MODEL_NAME = "hamzab/roberta-fake-news-classification"

classifier = pipeline("text-classification", model=MODEL_NAME)

def get_credibility(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string.")
    result = classifier(text, truncation=True, max_length=512)[0]
    label_raw = result["label"].upper()
    score = result["score"]
    if "FAKE" in label_raw:
        label = "FAKE"
        confidence = score
        real_prob = 1 - score
    else:
        label = "REAL"
        confidence = score
        real_prob = score
    return {
        "label": label,
        "raw_score": round(real_prob * 100, 2),
        "confidence": round(confidence, 4)
    }

if __name__ == "__main__":
    samples = [
        ("SHOULD BE REAL", "NASA has confirmed that the James Webb Space Telescope captured the deepest infrared image of the universe ever taken."),
        ("SHOULD BE FAKE", "BREAKING: Scientists confirm that 5G towers are secretly implanting microchips in people through the air."),
        ("SHOULD BE FAKE", "Doctors HATE this man! Local teacher cures cancer overnight using one weird trick Big Pharma hides."),
    ]
    print(f"Model  : {MODEL_NAME}")
    print("-" * 55)
    for tag, text in samples:
        result = get_credibility(text)
        expected = "REAL" if "REAL" in tag else "FAKE"
        icon = "OK" if result["label"] == expected else "WRONG"
        print(f"[{icon}] {tag}")
        print(f"   Label      : {result['label']} (expected {expected})")
        print(f"   Raw score  : {result['raw_score']}%")
        print(f"   Confidence : {result['confidence']}")
        print()
