import requests
import json

url = "http://localhost:8000/api/v1/analyze"
payload = {
    "content_type": "text",
    "text": "Hello world"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
