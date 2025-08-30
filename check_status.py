#!/usr/bin/env python3
"""
Quick WhatsApp status checker
"""
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

def check_status():
    instance_id = os.getenv("WHATSAPP_INSTANCE_ID")
    token = os.getenv("WHATSAPP_TOKEN")
    
    status_url = f"https://api.green-api.com/waInstance{instance_id}/getStateInstance/{token}"
    
    try:
        response = requests.get(status_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            state = data.get('stateInstance')
            
            print(f"📱 WhatsApp Instance Status: {state}")
            
            if state == 'authorized':
                print("✅ READY! Your WhatsApp bot is authorized and ready to receive messages!")
                return True
            elif state == 'starting':
                print("🔄 Still starting... Please wait and try again in a few minutes")
                return False
            elif state == 'notAuthorized':
                print("❌ Not authorized. Please scan the QR code:")
                print("🔗 https://api.green-api.com/waInstance7105219783/qr/8a2bac7488884cfdaacf9c83f0ce5dd715801ff16dac411dbf")
                return False
            else:
                print(f"⚠️ Unknown state: {state}")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    print("Checking WhatsApp authorization status...")
    check_status()
