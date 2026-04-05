# 🧠 MisLEADING — The Brain Behind the App (How it Works)

Ye document saare team members (especially Member 1, 2, aur 3) ke reference ke liye hai. Isme explain kiya gaya hai ki hamara AI alag-alag type ke data (Text, Image, Video, URL) ko kaise handle karta hai **bina users ki privacy tode**.

---

## 1️⃣ TEXT ANALYSIS (Fake News & Propaganda)
**Flow:** User ne text bheja ➡️ Fast Brain (ML) scan karega ➡️ Deep Brain (LLM) verify karega.

1. **The Fast Brain (Scikit-Learn ML Model):**
   * Jaise hi text aayega, hamara `model.pkl` usko fractions of a second mein check karega ki usme Fake News wali language hai ya nahi (e.g., *"URGENT Share this before govt deletes it"*).
   * Ye Turant ek **Probability Score (0-100%)** dega.
2. **The Deep Brain (Claude 3.5 Sonnet API):**
   * Agar score high risk ka hua, toh aage Claude LLM ke pas jayega.
   * Claude uska 'Context' samjhega (Kya kisi community ke khilaf bhashan hai? Kya emotions manipulate kiye jaa rahe hain?). Ye directly 3 reasons (bullet points) return karega jo user ko frontend pe dikhayenge.

---

## 2️⃣ IMAGE ANALYSIS & PRIVACY LOGIC (Nudes, Leaks & Deepfakes)
**Problem:** Hum users ke private pictures server pe store nahi kar sakte. To AI ko kaise pata chalega konsi photo viral fake news/leak hai aur konsi normal private selfie?

**Solution: "Hash Velocity Tracking" (Privacy-First Scanning)**
1. **The Hash (Fingerprint):** Jab bhi frontend se photo aayegi, photo actual me backend DB mein save hi nahi hogi. Photo ka ek **Hash/Code (`X78KPL2`)** banega.
2. **The Counter (Virality Test):** Server sirf check karega ye hash kitni baar forward ho raha hai.
   * **Count < 10 (Private):** Matlab family/friends me share ho rahi hai. AI us file ko RAM se 0.1s mein delete kar dega.
   * **Count > 50 (Viral Leak / Fake Meme):** System flag kar dega ki ye image "Viral" ho chuki hai.
3. **The AI Trigger (Claude Vision):** Jab image viral flag ho jayegi, TAB Claude Vision aur Sightengine activate honge.
   * Wo check karenge: Kya ye photo AI-Generated hai? Kya isme NSFW / Nudity hai? Kya isme hate speech text (OCR) likha hai? 
   * Agar unsafe nikli, us Hash ko Global Blocklist me daal diya jayega aur Frontend par RED FLAG 🚨 dikhne lagega. Admin panel par bhi image nahi dikhegi, sirf Hash Id aur "Threat" type dikhega.

---

## 3️⃣ VIDEO ANALYSIS (Morphed Clips & Misleading Context)
Videos ko analyze karna sabse lamba process hota hai, toh usko optimise kiya gaya hai.
**Flow:**
1. **Frame Extraction:** Pura video backend pe download/play nahi hoga. Video ke beech mein se 3 alag-alag Frames (Photos) randomly extract ki jayengi.
2. **Keyframe Analysis:** Un 3 photos ko `image_analyzer.py` (Claude Vision) mein bheja jayega. E.g. agar news anchor ki mooh ki lip-sync nahi ho rahi (Deepfake) ya background aur text mismatch kar raha hai.
3. **Audio Transcript (Future Extension):** Video ki thodi si audio nikal ke verify ki jayegi bhashan fake toh nahi.

---

## 4️⃣ URL / LINK ANALYSIS (Phishing & Scams)
Fake lottery ya malware links ka logic bilkul straight hai:
1. **Google Safe Browsing & VirusTotal APIs:** Link aate hi unko real-time check kiya jata hai in top engines par ki kahi "Malware" ya "Phishing" fraud report toh nahi hua.
2. **Domain Age Test:** Whois api se dekhte hain domain kab bana. E.g. "free-jio-recharge.com" agar sirf 2 din pehle bana hai, toh instantly `Risk Score + 30` aur **FAKE** flag lagega kyu ki scammer hamesha naye domains banate hain.

---

### 🔥 THE WRAPPER (Final Risk Engine)
*(By Member 2)*
Ye saare parts independent chalte hain aur aakhir mein **`ai_wrapper/wrapper.py`** me combine hote hain. 
* ML Text (30 marks) + URL Check (30 marks) + Claude Reasoning (40 marks).
* **Final formula:** Jiska score 0-30 = Green (Safe), 31-60 = Orange (Misleading), 61-100 = Red (Fake News).

Ye document padh ke sabhi members apna apna module sync karenge! Happy Coding!
