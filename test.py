import requests

payload = {"title":"Custom API Events ", "text": "Failure Redeploying Service Duration", "duration": 10000, "severity": 5}
url = 'http://localhost:42699/com.instana.plugin.generic.event'

r = r = requests.post(url, json=payload)