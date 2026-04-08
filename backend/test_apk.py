import asyncio
import json
import base64
from analyzers import apk_analyzer

async def main():
    print("=== TEST 1: CLEAN PDF FILE ===")
    # PDF magic bytes: %PDF
    clean_pdf_data = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj"
    payload_pdf = f"data:application/pdf;base64,{base64.b64encode(clean_pdf_data).decode('utf-8')}"
    
    result = await apk_analyzer.analyze(payload_pdf)
    print("Clean PDF Result:")
    print(json.dumps(result, indent=2))

    print("\n=== TEST 2: MALICIOUS DISGUISED EXE ===")
    # MZ header (Windows Executable) disguised as something else
    malicious_exe_data = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
    payload_exe = f"data:application/octet-stream;base64,{base64.b64encode(malicious_exe_data).decode('utf-8')}"
    
    result2 = await apk_analyzer.analyze(payload_exe)
    print("Malicious EXE Result:")
    print(json.dumps(result2, indent=2))

    print("\n=== TEST 3: VIRUSTOTAL HASH HIT (EICAR TEST) ===")
    # EICAR test string is often flagged by AVs
    eicar_string = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    payload_eicar = f"data:text/plain;base64,{base64.b64encode(eicar_string).decode('utf-8')}"
    
    result3 = await apk_analyzer.analyze(payload_eicar)
    print("EICAR (VirusTotal) Result:")
    print(json.dumps(result3, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
