"""
ML Model Training Script — Run once to generate model.pkl
Uses LIAR dataset or built-in sample data for quick start
"""
import os
import re
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split


def preprocess(text: str) -> str:
    """Clean text for ML processing"""
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+', '', text)       # Remove URLs
    text = re.sub(r'@\w+', '', text)                  # Remove mentions
    text = re.sub(r'[^a-z\s]', '', text)              # Remove special chars
    text = re.sub(r'\s+', ' ', text).strip()           # Remove extra spaces
    return text


def train_with_liar_dataset(tsv_path: str):
    """Train using LIAR dataset TSV file"""
    import pandas as pd
    
    df = pd.read_csv(tsv_path, sep='\t', header=None,
        names=['id', 'label', 'statement', 'subject', 'speaker',
               'job', 'state', 'party', 'barely_true', 'false',
               'half_true', 'mostly_true', 'pants_fire', 'context'])
    
    # Map 6 labels to 3 classes
    label_map = {
        'pants-fire': 'fake', 'false': 'fake',
        'barely-true': 'misleading', 'half-true': 'misleading',
        'mostly-true': 'real', 'true': 'real'
    }
    df['label3'] = df['label'].map(label_map)
    df = df.dropna(subset=['label3', 'statement'])
    df['clean'] = df['statement'].apply(preprocess)
    
    return df['clean'].values, df['label3'].values


def train_with_sample_data():
    """
    Built-in sample training data for quick start.
    Uses common misinformation patterns found in WhatsApp forwards.
    """
    fake_texts = [
        "breaking news doctors dont want you to know this cure",
        "urgent share this before it gets deleted by government",
        "forward to everyone you know this message will save lives",
        "scientists confirm drinking hot water cures all diseases",
        "this secret the media is hiding from you must share now",
        "government is hiding the truth share before they delete",
        "miracle cure discovered big pharma trying to suppress it",
        "breaking nasa confirms world ending next week share now",
        "doctors exposed this natural remedy they want banned",
        "share immediately this warning could save your family",
        "proof that vaccines cause dangerous side effects exposed",
        "leaked document reveals government conspiracy confirmed",
        "urgent warning do not ignore this message forward to all",
        "shocking truth mainstream media refuses to report this",
        "pass this along the internet is trying to censor this",
        "free money giveaway just forward this to ten people now",
        "natural remedy they dont want you to discover share fast",
        "exposed celebrity death cover up mainstream media silent",
        "warning this food product is poisoning your children act",
        "must read before deleted the cure they are suppressing",
        "china created this virus as biological weapon confirmed",
        "bill gates microchip in vaccines exposed document leaked",
        "five g towers causing cancer government admits truth now",
        "drinking bleach cures covid share this life saving info",
        "election was rigged proof found share before censored",
    ]
    
    misleading_texts = [
        "studies suggest possible link between diet and health outcomes",
        "some experts question the effectiveness of certain policies",
        "preliminary research indicates potential benefits need more study",
        "unverified reports claim new discovery in medical science field",
        "according to unnamed sources government considering new policy",
        "early data shows promising results but peer review is pending",
        "controversial opinion piece argues against mainstream thinking",
        "anecdotal evidence suggests alternative approach may have merit",
        "disputed study claims connection between two unrelated things",
        "one doctor claims this treatment works better than standard care",
        "viral post makes partially true claims about health benefits",
        "misleading headline exaggerates findings of actual research paper",
        "out of context quote makes politician appear to say something different",
        "old news article shared as if it were a current breaking story",
        "real statistics presented without important context or comparison",
    ]
    
    real_texts = [
        "the world health organization recommends regular hand washing",
        "according to published peer reviewed research in nature journal",
        "government officials announced new policy changes effective today",
        "reuters reports economic growth steady at three percent this quarter",
        "university researchers published findings in scientific american",
        "bbc reports on climate summit outcomes with expert analysis",
        "supreme court ruling establishes new precedent in landmark case",
        "census data shows population trends over the past decade analysis",
        "medical journal lancet publishes results of clinical trial study",
        "associated press confirms election results certified by officials",
        "new york times investigation reveals corporate financial practices",
        "official press release from ministry of health on vaccination drive",
        "published research paper in peer reviewed journal on disease treatment",
        "central bank announces interest rate decision with economic data",
        "scientific consensus confirms human activity contributes to warming",
        "world bank releases annual report on global poverty statistics data",
        "national weather service issues forecast based on satellite data",
        "verified fact check organizations confirm the claim is accurate",
        "audited financial statements released by publicly traded company",
        "academic study with large sample size confirms previous findings",
    ]
    
    texts = fake_texts + misleading_texts + real_texts
    labels = (
        ['fake'] * len(fake_texts) + 
        ['misleading'] * len(misleading_texts) + 
        ['real'] * len(real_texts)
    )
    
    return np.array(texts), np.array(labels)


def train_model():
    """Train the ML model and save to disk"""
    print("🧠 MisLEADING — ML Model Training")
    print("=" * 50)
    
    # Check for LIAR dataset
    liar_path = os.path.join(os.path.dirname(__file__), "liar_dataset", "train.tsv")
    
    if os.path.exists(liar_path):
        print("📂 Found LIAR dataset — training on full data...")
        texts, labels = train_with_liar_dataset(liar_path)
    else:
        print("📂 LIAR dataset not found — using built-in sample data...")
        print("   (Download LIAR dataset for better accuracy)")
        texts, labels = train_with_sample_data()
    
    print(f"   Total samples: {len(texts)}")
    print(f"   Classes: {dict(zip(*np.unique(labels, return_counts=True)))}")
    
    # Preprocess
    clean_texts = [preprocess(t) for t in texts]
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        clean_texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    # Build pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=10000,
            min_df=1,
            max_df=0.95,
        )),
        ('clf', LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            C=1.0,
            random_state=42,
        )),
    ])
    
    # Train
    print("\n🔄 Training pipeline...")
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    train_acc = pipeline.score(X_train, y_train)
    test_acc = pipeline.score(X_test, y_test)
    print(f"   Train accuracy: {train_acc:.2%}")
    print(f"   Test accuracy:  {test_acc:.2%}")
    
    # Save
    model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
    joblib.dump(pipeline, model_path)
    print(f"\n✅ Model saved to: {model_path}")
    
    # Quick test
    print("\n🧪 Quick test predictions:")
    test_inputs = [
        "URGENT share this cure before government deletes it",
        "BBC reports economic growth at steady pace this quarter",
        "some experts question the findings of this study",
    ]
    for text in test_inputs:
        pred = pipeline.predict([preprocess(text)])[0]
        probs = pipeline.predict_proba([preprocess(text)])[0]
        max_prob = max(probs)
        print(f"   '{text[:50]}...' → {pred.upper()} ({max_prob:.0%})")
    
    print("\n🎉 Training complete!")
    return pipeline


if __name__ == "__main__":
    train_model()
