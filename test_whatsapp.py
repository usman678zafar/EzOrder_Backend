#!/usr/bin/env python3
"""
Test WhatsApp Green API connection
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_whatsapp_connection():
    """Test WhatsApp Green API connection and status"""
    instance_id = os.getenv("WHATSAPP_INSTANCE_ID")
    token = os.getenv("WHATSAPP_TOKEN")
    
    if not instance_id or not token:
        print("❌ Missing WhatsApp credentials in .env file")
        return False
    
    print(f"Testing WhatsApp connection...")
    print(f"Instance ID: {instance_id}")
    print(f"Token: {token[:20]}...")
    
    # Test 1: Check instance status
    try:
        status_url = f"https://api.green-api.com/waInstance{instance_id}/getStateInstance/{token}"
        print(f"\n[INFO] Checking instance status...")
        print(f"URL: {status_url}")
        
        response = requests.get(status_url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Instance Status: {data}")
            
            state = data.get('stateInstance')
            if state == 'authorized':
                print("✅ WhatsApp instance is authorized and ready!")
            elif state == 'notAuthorized':
                print("❌ WhatsApp instance is NOT authorized!")
                print("📱 Please scan QR code to authorize your WhatsApp instance")
                return False
            elif state == 'starting':
                print("🔄 WhatsApp instance is starting up...")
                print("⏳ Please wait a few minutes for the instance to fully start")
                print("📱 You may need to scan QR code if this is the first time")
                return False
            elif state == 'sleepMode':
                print("😴 WhatsApp instance is in sleep mode")
                print("💡 Send a message to wake it up or restart the instance")
                return False
            else:
                print(f"⚠️ Unknown instance state: {state}")
                print("📖 Possible states: authorized, notAuthorized, starting, sleepMode")
                
        else:
            print(f"❌ Failed to get instance status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking instance status: {str(e)}")
        return False
    
    # Test 2: Check webhook settings
    try:
        webhook_url = f"https://api.green-api.com/waInstance{instance_id}/getSettings/{token}"
        print(f"\n🔍 Checking webhook settings...")
        
        response = requests.get(webhook_url, timeout=10)
        if response.status_code == 200:
            settings = response.json()
            print(f"✅ Webhook Settings: {settings}")
            
            # Check if incoming webhooks are enabled
            if settings.get('incomingWebhook') == 'yes':
                print("✅ Incoming webhooks are enabled")
            else:
                print("⚠️ Incoming webhooks are disabled - this might cause issues")
                
        else:
            print(f"❌ Failed to get webhook settings: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking webhook settings: {str(e)}")
    
    # Test 3: Test receiving notifications
    try:
        receive_url = f"https://api.green-api.com/waInstance{instance_id}/receiveNotification/{token}"
        print(f"\n🔍 Testing notification receiving...")
        
        response = requests.get(receive_url, timeout=5)
        print(f"Receive Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data is None:
                print("✅ No pending notifications (this is normal)")
            else:
                print(f"📨 Received notification: {data}")
        else:
            print(f"❌ Failed to receive notifications: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing notifications: {str(e)}")

    return True

def get_qr_code():
    """Get QR code for WhatsApp authorization"""
    instance_id = os.getenv("WHATSAPP_INSTANCE_ID")
    token = os.getenv("WHATSAPP_TOKEN")

    try:
        qr_url = f"https://api.green-api.com/waInstance{instance_id}/qr/{token}"
        print(f"\n📱 Getting QR code for authorization...")
        print(f"QR URL: {qr_url}")

        response = requests.get(qr_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('type') == 'qrCode':
                print("✅ QR Code received!")
                print(f"📱 QR Code: {data.get('message')}")
                print("\n🔗 Open this link in your browser to see the QR code:")
                print(f"   {qr_url}")
                print("\n📱 Steps to authorize:")
                print("1. Open WhatsApp on your phone")
                print("2. Go to Settings > Linked Devices")
                print("3. Tap 'Link a Device'")
                print("4. Scan the QR code from the URL above")
                return True
            else:
                print(f"⚠️ Unexpected QR response: {data}")
                return False
        else:
            print(f"❌ Failed to get QR code: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error getting QR code: {str(e)}")
        return False

def test_whatsapp_library():
    """Test if the WhatsApp library is working"""
    try:
        from whatsapp_chatbot_python import GreenAPIBot
        print("[SUCCESS] whatsapp_chatbot_python library imported successfully")
        
        instance_id = os.getenv("WHATSAPP_INSTANCE_ID")
        token = os.getenv("WHATSAPP_TOKEN")
        
        # Try to create bot instance
        bot = GreenAPIBot(instance_id, token)
        print("[SUCCESS] GreenAPIBot instance created successfully")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Failed to import whatsapp_chatbot_python: {e}")
        print("[INFO] Try: pip install whatsapp-chatbot-python")
        return False
    except Exception as e:
        print(f"[ERROR] Error creating bot instance: {e}")
        return False

def main():
    print("WhatsApp Green API Connection Test")
    print("=" * 50)
    
    # Test library import
    library_ok = test_whatsapp_library()
    
    print("\n" + "=" * 50)
    
    # Test API connection
    if library_ok:
        api_ok = test_whatsapp_connection()
    else:
        api_ok = False
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"Library Import: {'✅ OK' if library_ok else '❌ Failed'}")
    print(f"API Connection: {'✅ OK' if api_ok else '❌ Failed'}")
    
    if not library_ok or not api_ok:
        print("\n🔧 Troubleshooting:")
        if not library_ok:
            print("1. Install WhatsApp library: pip install whatsapp-chatbot-python")
        if not api_ok:
            print("2. Check your WhatsApp instance authorization")
            print("3. Verify WHATSAPP_INSTANCE_ID and WHATSAPP_TOKEN in .env")
            print("4. Make sure your Green API account is active")

            # Offer to get QR code
            print("\n📱 Would you like to get the QR code for authorization?")
            try:
                choice = input("Enter 'y' to get QR code, or any other key to skip: ").lower()
                if choice == 'y':
                    get_qr_code()
            except KeyboardInterrupt:
                print("\n👋 Cancelled by user")

if __name__ == "__main__":
    main()
