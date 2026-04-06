import json
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os

# Config
DATA_FILE = "data/synthetic_dataset.jsonl"
MODEL_FILE = "models/custom_lang_id.joblib"

def load_data(file_path):
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return pd.DataFrame(data)

def train():
    print(f"📦 Loading dataset from {DATA_FILE}...")
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: Dataset file not found!")
        return

    df = load_data(DATA_FILE)
    print(f"📊 Dataset Stats:\n{df['label'].value_counts()}")

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        df['text'], df['label'], test_size=0.2, random_state=42
    )

    # Build Pipeline (TF-IDF + Naive Bayes)
    # Using char-level n-grams (2-5) is great for language ID
    model = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char', ngram_range=(2, 5))),
        ('clf', MultinomialNB())
    ])

    print("🧠 Training the 'Student' Language Model...")
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    print("\n📈 Evaluation Report:")
    print(classification_report(y_test, y_pred))

    # Save
    os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
    joblib.dump(model, MODEL_FILE)
    print(f"✅ Model saved to {MODEL_FILE}")

if __name__ == "__main__":
    train()
