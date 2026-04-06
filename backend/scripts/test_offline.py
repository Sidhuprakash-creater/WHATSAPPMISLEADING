import joblib
import os
import re

# Config
MODEL_PATH = "models/custom_lang_id.joblib"
HINGLISH_DICTIONARY = ["kya", "hai", "tum", "nahi", "mil raha", "scheme", "free", "baat", "kaise"]

def check_hinglish_heuristics(text: str) -> bool:
    text_lower = text.lower()
    match_count = 0
    for word in HINGLISH_DICTIONARY:
        if re.search(rf'\b{word}\b', text_lower):
            match_count += 1
    return match_count >= 2

def test():
    print("🧠 Testing 'Deeply Trained' Language Model (Offline)...")
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Model {MODEL_PATH} not found!")
        return

    model = joblib.load(MODEL_PATH)
    
    test_cases = [
        {"input": "Yeh free scheme hai", "expected": "hinglish"},
        {"input": "This is fake news", "expected": "english"},
        {"input": "यह एक झूठी खबर है", "expected": "hindi"},
        {"input": "ଏହା ଏକ ଭୁଲ ସନ୍ଦେଶ", "expected": "odia"}
    ]

    for case in test_cases:
        text = str(case["input"]).lower()
        text = re.sub(r'[^\w\s]', '', text).strip()
        
        prediction = model.predict([text])[0]
        
        # Apply Hinglish Heuristic for comparison
        if prediction == "english" or prediction == "hinglish":
            if check_hinglish_heuristics(case["input"]):
                prediction = "hinglish"
        
        status = "✅ PASS" if prediction == case["expected"] else f"❌ FAIL (Got: {prediction})"
        print(f"{status} | Input: '{case['input']}'")

if __name__ == "__main__":
    test()
