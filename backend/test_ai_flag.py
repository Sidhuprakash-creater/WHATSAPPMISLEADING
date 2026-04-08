import requests
import base64
import json
import sys

# use a tiny transparent 1x1 png
png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
b64_img = base64.b64encode(png_data).decode('utf-8')

res = requests.post(
    'http://localhost:8000/api/v1/analyze', 
    json={'file_url': f"data:image/png;base64,{b64_img}", 'content_type': 'image'}
)

data = res.json()
print("Score:", data.get('risk_score'))
print("AI Generated Flag:", data.get('explanation', {}).get('is_ai_generated'))
print("Media Scan Details:", json.dumps(data.get('signals', {}).get('media', {}), indent=2))
