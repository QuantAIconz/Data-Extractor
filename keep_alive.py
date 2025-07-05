#!/usr/bin/env python3
"""
Keep-alive script for Render deployment
This script pings the health endpoint every 10 minutes to keep the service alive
"""

import requests
import time
import os
from datetime import datetime

def ping_health_endpoint(url):
    """Ping the health endpoint"""
    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            print(f"[{datetime.now()}] ✅ Health check successful: {response.json()}")
            return True
        else:
            print(f"[{datetime.now()}] ❌ Health check failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Health check error: {str(e)}")
        return False

def main():
    # Get the URL from environment variable or use a default
    app_url = os.environ.get('APP_URL', 'https://your-app-name.onrender.com')
    
    print(f"🚀 Starting keep-alive script for: {app_url}")
    print(f"⏰ Will ping every 30 seconds to keep the service alive")
    
    while True:
        ping_health_endpoint(app_url)
        # Wait 30 seconds before next ping
        time.sleep(30)

if __name__ == "__main__":
    main() 