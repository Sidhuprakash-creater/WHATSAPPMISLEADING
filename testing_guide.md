# 🧪 MisLEADING: Testing & Deployment Guide

This guide provides the exact commands to verify your backend analysis, test the new safety features, and launch the mobile app on your device.

---

## 1. Backend Verification (API)
Ensure your backend is running. If not, start it with:
```powershell
# In the root directory (d:\WHATSAPPMISLEADING)
python backend/main.py
```

### ✅ Test 1: Text Analysis (Real Claim)
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"content_type": "text", "text": "Drinking hot water cures COVID-19."}'
```

### ✅ Test 2: Image Analysis (AI Forensic)
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"content_type": "image", "file_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg"}'
```

---

## 2. Safety Guard Verification (New!)
We have implemented a **Real-Time Safety Logic** that blocks offensive language.

### 🛡️ Test 3: Profanity Block (Backend)
Try sending a restricted word (e.g., using "badword1" as a placeholder for restricted Hindi/English slang):
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"content_type": "text", "text": "This is a badword1"}'
```
**Expected Result**: You should receive a `400 Bad Request` with a safety warning:
> ⚠️ Safety Warning: Offensive language is not allowed in MisLEADING.

---

## 3. Run Mobile App on Device
To test the **Auto-Delete Keyboard** and **Warning Popups** on your phone or emulator:

### 📱 Step-by-Step Deployment:
1.  **Connect your Device**: Plug in your Android phone (with USB debugging ON) or start your Emulator.
2.  **Verify Connection**:
    ```powershell
    adb devices
    ```
3.  **Launch the App**:
    ```powershell
    # From the mobile directory
    cd mobile
    flutter run
    ```

### ⌨️ Testing the Smart Keyboard:
1.  Open the MisLEADING app on your phone.
2.  Go to the chat input bar.
3.  Type a restricted word (e.g., common Hindi or English slang).
4.  **Observer Behavior**:
    *   The word will be **instantly deleted** from the text field.
    *   A **red warning popup** will appear at the bottom explaining the violation.

---

## 🚀 Pro Tip: Health Check
Run this to see if all AI modules (Gemini, Redis, ML) are online:
```bash
curl http://localhost:8000/health
```
