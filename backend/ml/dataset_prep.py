import json
import os
import random

# Ensure data directory exists
os.makedirs("backend/data", exist_ok=True)

OUTPUT_FILE = "backend/data/llm_instruction_dataset.jsonl"

# The master system prompt representing our expected behavior for the local Ollama LLM
SYSTEM_PROMPT = """You are MisLEADING AI, an advanced intelligence engine designed to protect users from misinformation, scams, toxicity, and harmful intent on WhatsApp. 
Analyze the user's message meticulously. Output a JSON object with strictly these keys:
{
    "detected_language": "English/Hindi/Hinglish/Odia/etc",
    "content_category": "Fake News / Scam / Promotional / Normal / Toxic",
    "intent_to_harm": boolean,
    "severity_score": int (0-100),
    "explanation": "Brief explanation of why"
}"""

# A curated set of high-quality examples spanning different languages, especially Hindi/Regional scams
TRAINING_SAMPLES = [
    # --- Hindi / Hinglish Scams & Fake News ---
    {
        "input": "KBC me aapka 25 lakh ka lottery laga hai. WhatsApp call par manager aakash wma se sampark karein: +923XXXX. Processing fee 5000 jama karein warna 25 lakh cancel ho jayega.",
        "output": {
            "detected_language": "Hinglish",
            "content_category": "Scam",
            "intent_to_harm": True,
            "severity_score": 95,
            "explanation": "Classic KBC lottery scam demanding advance fee. Uses international calling code (+92) typical of WhatsApp scams."
        }
    },
    {
        "input": "Jio users ke liye khushkhabri! Mukesh Ambani ka birthday offer. Is link par click karein aur payein 3 mahine ka free recharge: http://free-jio-recharge.xyz Jaldi karein, sirf 1 ghanta bacha hai!",
        "output": {
            "detected_language": "Hinglish",
            "content_category": "Scam",
            "intent_to_harm": True,
            "severity_score": 90,
            "explanation": "Phishing scam disguised as a telecom recharge offer. Uses artificial urgency and a highly suspicious unofficial URL."
        }
    },
    {
        "input": "प्रिय ग्राहक, आपका SBI YONO अकाउंट ब्लॉक कर दिया गया है क्योंकि आपका PAN अपडेट नहीं है. तुरंत अपना PAN अपडेट करने के लिए इस लिंक पर जाएँ: http://sbi-kyc-update-auth.com",
        "output": {
            "detected_language": "Hindi",
            "content_category": "Scam",
            "intent_to_harm": True,
            "severity_score": 98,
            "explanation": "High-risk banking phishing scam. Tries to steal banking credentials mimicking SBI KYC requirements."
        }
    },
    {
        "input": "अस्पताल में ऑक्सीजन खत्म हो गई है, सरकार कुछ नहीं कर रही. इस मैसेज को 10 ग्रुप में भेजो ताकि सरकार की नींद खुले! अगर सच्चे हिंदुस्तानी हो तो शेयर करो!",
        "output": {
            "detected_language": "Hindi",
            "content_category": "Fake News",
            "intent_to_harm": False,
            "severity_score": 75,
            "explanation": "Propaganda/Misinformation containing viral pressure ('Share to 10 groups') and emotional guilt-tripping."
        }
    },
    {
        "input": "Work from home part-time job! Earn ₹5000 to ₹10000 daily by simply liking YouTube videos. Reply 'YES' to start. Registration fee only ₹500.",
        "output": {
            "detected_language": "English",
            "content_category": "Scam",
            "intent_to_harm": True,
            "severity_score": 90,
            "explanation": "Typical Telegram/WhatsApp task scam. Lures victims with easy tasks, builds trust, then steals money as 'registration fees'."
        }
    },
    
    # --- Toxic / Dangerous Intent ---
    {
        "input": "Saale tu agar us ilake me dikh gaya na toh tujhe aur tere purre parivar ko zinda jala dunga. Yaad rakhna meri baat.",
        "output": {
            "detected_language": "Hinglish",
            "content_category": "Toxic",
            "intent_to_harm": True,
            "severity_score": 100,
            "explanation": "Extremely toxic. Direct death and arson threat to the user and their family. Absolute intent to harm."
        }
    },
    {
        "input": "Tumi ekta boka choda. Toder jonne desh ta nosto hocche. Shobai k mere fela uchit.",
        "output": {
            "detected_language": "Bengali",
            "content_category": "Toxic",
            "intent_to_harm": True,
            "severity_score": 95,
            "explanation": "Contains abusive language and incites mass violence. High threat level."
        }
    },
    
    # --- Genuine / Normal ---
    {
        "input": "Bhai kal sham ko football khelne chalenge turf pe? 6 baje ka slot book kiya hai.",
        "output": {
            "detected_language": "Hinglish",
            "content_category": "Normal",
            "intent_to_harm": False,
            "severity_score": 0,
            "explanation": "A normal casual conversation arranging a sports meetup."
        }
    },
    {
        "input": "ଆଜି ସନ୍ଧ୍ୟାରେ ମାର୍କେଟ୍ ଯିବି, କିଛି ଆଣିବାର ଅଛି କି?",
        "output": {
            "detected_language": "Odia",
            "content_category": "Normal",
            "intent_to_harm": False,
            "severity_score": 0,
            "explanation": "Standard daily communication asking if anything is needed from the market."
        }
    },
    
    # --- Promotional (Annoying but not Scam) ---
    {
        "input": "Diwali Dhamaka Sale! Flat 50% Off on all electronics at Reliance Digital. Visit your nearest store today. Valid till Sunday.",
        "output": {
            "detected_language": "English",
            "content_category": "Promotional",
            "intent_to_harm": False,
            "severity_score": 20,
            "explanation": "Legitimate promotional advertisement for a major retail store. Not financially harmful, just marketing."
        }
    },
    
    # --- Regional Scams & Fake News (Extended) ---
    {
        "input": "നിങ്ങളുടെ ബാങ്ക് അക്കൗണ്ട് മരവിപ്പിച്ചു. ഉടൻ തന്നെ പാൻ കാർഡ് അപ്ഡേറ്റ് ചെയ്യാൻ ഈ ലിങ്കിൽ ക്ലിക്ക് ചെയ്യുക: http://update-pan-kerala.com/login",
        "output": {
            "detected_language": "Malayalam",
            "content_category": "Scam",
            "intent_to_harm": True,
            "severity_score": 95,
            "explanation": "Financial phishing scam in Malayalam demanding immediate PAN card update via a malicious link."
        }
    },
    {
        "input": "మీ WhatsApp లక్కీ డ్రాలో 5 లక్షలు గెలుచుకున్నారు! బహుమతి పొందడానికి ఈ నంబర్‌కు Google Pay ద్వారా ₹2000 పన్ను చెల్లించండి.",
        "output": {
            "detected_language": "Telugu",
            "content_category": "Scam",
            "intent_to_harm": True,
            "severity_score": 98,
            "explanation": "WhatsApp lucky draw scam in Telugu. Asks for advance tax payment via UPI to claim a fake prize."
        }
    },
    {
        "input": "அரசு இலவச மடிக்கணினி திட்டம் 2024! கீழ்க்கண்ட லிங்கை க்ளிக் செய்து உங்கள் விவரங்களை பதிவு செய்யவும். அனைவருக்கும் இலவசம்! http://tn-free-laptops.freebies.xyz",
        "output": {
            "detected_language": "Tamil",
            "content_category": "Scam",
            "intent_to_harm": True,
            "severity_score": 85,
            "explanation": "Fake government scheme scam in Tamil collecting personal data under the guise of distributing free laptops."
        }
    },
    {
        "input": "कोरोनाची नवीन लाट आली आहे! कांद्याचा रस पिल्याने कोरोना 100% बरा होतो. हा मेसेज तुमच्या सर्व नातेवाईकांना पाठवा.",
        "output": {
            "detected_language": "Marathi",
            "content_category": "Fake News",
            "intent_to_harm": False,
            "severity_score": 80,
            "explanation": "Medical misinformation in Marathi suggesting a fake homemade cure for a serious disease. Highly misleading."
        }
    },
    {
        "input": "આ વ્હોટ્સએપ મેસેજ 11 લોકોને મોકલો અને તમને સાંજે સારા સમાચાર મળશે. નહી મોકલો તો નુકસાન થશે.",
        "output": {
            "detected_language": "Gujarati",
            "content_category": "Fake News",
            "intent_to_harm": False,
            "severity_score": 40,
            "explanation": "Chain letter/superstition message in Gujarati. It causes spam but no direct harm or financial loss."
        }
    },
    {
        "input": "Electricity connection will be disconnected tonight at 9:30 PM from the main office because your previous month's bill was not updated. Contact the electricity officer at 9876543210 immediately.",
        "output": {
            "detected_language": "English",
            "content_category": "Scam",
            "intent_to_harm": True,
            "severity_score": 95,
            "explanation": "Classic electricity bill disconnection scam. Creates panic and urges calling a fraudulent number."
        }
    }
]

def generate_instruction_dataset():
    print(f"🔄 Generating Instruction Tuning dataset for LLM Training...")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for sample in TRAINING_SAMPLES:
            # We use Llama-3 instruction format (or generic dictionary for datasets library)
            record = {
                "instruction": SYSTEM_PROMPT,
                "input": sample["input"],
                "output": json.dumps(sample["output"], ensure_ascii=False)
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
    print(f"✅ Generated {len(TRAINING_SAMPLES)} robust multimodal LLM training pairs at {OUTPUT_FILE}")
    print("   Ready for LoRA Fine-Grained Fine-Tuning!")

if __name__ == "__main__":
    generate_instruction_dataset()
