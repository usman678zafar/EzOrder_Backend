from whatsapp_chatbot_python import GreenAPIBot, Notification
from agents import Runner
from config.database import db
from services.conversation_service import ConversationService
from services.state_manager import StateManager
from agents_folder.restaurant_agent import AgentFactory
from agents_folder.registration_agent import RegistrationAgentFactory
from utils.phone_utils import clean_phone_number
from services.free_speech_service import HybridSpeechToTextService
from typing import Optional
import asyncio
import concurrent.futures
import threading
import nest_asyncio
import time

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

class WhatsAppHandler:
    def __init__(self, instance_id: str, token: str):
        self.bot = GreenAPIBot(instance_id, token)
        self.conversation_service = ConversationService()
        self.state_manager = StateManager
        self.speech_service = HybridSpeechToTextService()
        
        # Create both agents
        self.registration_agent, self.registration_config = RegistrationAgentFactory.create_registration_agent()
        self.restaurant_agent, self.restaurant_config = AgentFactory.create_restaurant_agent()
        
        # Thread pool for running agents with more workers for better concurrency
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
        self._setup_handlers()

    def _setup_handlers(self):
        @self.bot.router.message()
        def message_handler(notification: Notification) -> None:
            # Handle message in a separate thread to avoid blocking
            self.executor.submit(self._handle_message_wrapper, notification)

    def _handle_message_wrapper(self, notification: Notification):
        """Wrapper to handle exceptions in threaded execution"""
        try:
            self._handle_message(notification)
        except Exception as e:
            print(f"❌ Error in message handler wrapper: {e}")
            try:
                notification.answer("Sorry, I encountered an error. Please try again.")
            except:
                pass

    def _run_agent_safely(self, agent, context, config, agent_type="Agent"):
        """Run agent with proper event loop handling and improved timeout"""
        start_time = time.time()
        print(f"🤖 Starting {agent_type}...")
        
        def run_with_new_loop():
            """Run agent in a new event loop"""
            # Create new event loop for this execution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Run the agent
                result = Runner.run_sync(
                    starting_agent=agent,
                    input=context,
                    run_config=config
                )
                return result.final_output
            except Exception as e:
                print(f"❌ Error in {agent_type}: {e}")
                import traceback
                traceback.print_exc()
                raise e
            finally:
                # Clean up the loop
                loop.close()
        
        try:
            # Execute in thread pool with reduced timeout
            future = self.executor.submit(run_with_new_loop)
            # Reduced timeout from 30 to 15 seconds
            result = future.result(timeout=15)
            
            elapsed_time = time.time() - start_time
            print(f"✅ {agent_type} completed in {elapsed_time:.2f} seconds")
            return result
            
        except concurrent.futures.TimeoutError:
            elapsed_time = time.time() - start_time
            print(f"⏱ {agent_type} timed out after {elapsed_time:.2f} seconds")
            return f"🤖 I'm taking a bit longer than expected. Please try again or type 'menu' to see our offerings!"
        except Exception as e:
            print(f"❌ {agent_type} execution error: {e}")
            return f"🤖 I encountered an issue. Please try again or type 'menu' to see our offerings!"

    def _send_quick_acknowledgment(self, notification: Notification, phone_number: str):
        """Send immediate acknowledgment to user"""
        try:
            quick_responses = [
                "Got it! Let me process that for you... 🔄",
                "Thanks! Processing your request... ⏳",
                "Received! Just a moment... 💭",
                "On it! Getting that ready... 🚀"
            ]
            import random
            acknowledgment = random.choice(quick_responses)
            notification.answer(acknowledgment)
            return True
        except:
            return False

    def _handle_message(self, notification: Notification):
        try:
            # Extract and clean phone number
            raw_phone_number = notification.sender
            phone_number = clean_phone_number(raw_phone_number)
            
            # Debug: Print notification details
            print(f"📨 Received message from {phone_number}")
            
            # Get message data using the available method
            message_data = None
            if hasattr(notification, 'get_message_data'):
                try:
                    message_data = notification.get_message_data()
                except Exception as e:
                    print(f"❌ Error getting message data: {e}")
            
            # Check if it's a voice message
            is_voice_message = False
            if message_data and isinstance(message_data, dict):
                msg_type = message_data.get('typeMessage', '')
                is_voice_message = msg_type in ['audioMessage', 'voiceMessage', 'pttMessage']
                
                # Check fileMessageData for audio files
                if not is_voice_message and 'fileMessageData' in message_data:
                    file_data = message_data['fileMessageData']
                    if isinstance(file_data, dict):
                        mime_type = file_data.get('mimeType', '')
                        if 'audio' in mime_type or 'voice' in mime_type:
                            is_voice_message = True
            
            if is_voice_message:
                print(f"🎤 Processing voice message from {phone_number}")
                # Send quick acknowledgment for voice messages
                self._send_quick_acknowledgment(notification, phone_number)
                # Handle voice message
                message = self._process_voice_message(notification, phone_number)
                if not message:
                    print(f"❌ Voice processing failed for {phone_number}")
                    # Fallback message
                    message = "Hello"
                    # Notify user about the voice issue
                    self.conversation_service.save_conversation(
                        phone_number,
                        "assistant", 
                        "🎤 I received your voice message but couldn't process it clearly. How can I help you today?"
                    )
                else:
                    print(f"✅ Voice message processed: {message}")
            else:
                # Regular text message
                message = notification.message_text
                print(f"💬 Text message: {message}")
            
            # Ensure message is not None
            if not message:
                print(f"❌ Received empty message from {phone_number}")
                notification.answer("Sorry, I didn't receive any message. Please try again.")
                return
            
            # Save user message to conversation history
            self.conversation_service.save_conversation(phone_number, "user", message)
            
            # Clear old conversations periodically
            self.conversation_service.clear_old_conversations(phone_number)
            
            # Get user state
            print(f"🔍 Checking user state for {phone_number}...")
            user_state = self.state_manager.get_user_state(phone_number)
            user_exists = user_state['is_registered']
            user_data = user_state['user_data']
            
            print(f"👤 User registered: {user_exists}")
            if user_data:
                print(f"👤 User name: {user_data.get('name', 'Not set')}")
            
            # Get limited conversation history
            conversation_history = self.conversation_service.get_conversation_history(phone_number, limit=25)
            
            # Quick responses for common queries (no agent needed)
            lower_message = message.lower() if message else ""
            
            # Handle quick menu request
            if lower_message in ['menu', 'show menu', 'mnu', 'm']:
                from tools.menu_tools import show_menu_base  # Import base function
                quick_menu = show_menu_base()  # Use base function
                self.conversation_service.save_conversation(phone_number, "assistant", quick_menu)
                notification.answer(quick_menu)
                return



            # Handle quick order view
            
            if lower_message in ['view order', 'show cart', 'cart', 'my order']:
                    if user_exists:
                        from tools.order_tools import view_current_order_base  # Import base function
                        order_view = view_current_order_base(phone_number)  # Use base function
                        self.conversation_service.save_conversation(phone_number, "assistant", order_view)
                        notification.answer(order_view)
                        return


            
            if user_exists:
                # Existing user - use restaurant agent
                print(f"🍕 Using Restaurant Agent for existing user")
                
                # Check if this is likely a greeting or general message
                recent_messages = conversation_history.get('messages', [])
                
                # Count only USER messages to determine if it's a new session
                user_message_count = sum(1 for msg in recent_messages if msg.get('role') == 'user')
                is_new_session = user_message_count <= 1  # This is their first or second message
                
                # Determine user intent
                is_greeting = any(word in lower_message for word in 
                                ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 
                                 'good evening', 'salam', 'assalam', 'aoa'])
                
                is_confirmation = any(word in lower_message for word in 
                                    ['confirm', 'place order', 'yes confirm', 'checkout', 'proceed', "that's it", 'done'])
                is_view_order = any(word in lower_message for word in 
                                  ['view order', 'show cart', 'my order', 'current order'])
                is_adding_items = any(word in lower_message for word in 
                                    ['add', 'want', 'order']) and any(char.isdigit() for char in (message or ""))
                is_menu_request = any(word in lower_message for word in 
                                    ['menu', 'show menu', 'what do you have'])
                
                print(f"📊 Intent Analysis:")
                print(f"   - Greeting: {is_greeting}")
                print(f"   - Confirmation: {is_confirmation}")
                print(f"   - View Order: {is_view_order}")
                print(f"   - Adding Items: {is_adding_items}")
                print(f"   - Menu Request: {is_menu_request}")
                print(f"   - New Session: {is_new_session}")
                print(f"   - User message count: {user_message_count}")
                
                # Determine if we should show menu
                should_show_menu = is_new_session or is_greeting or is_menu_request
                
                # Create optimized context
                context = f"""
                CUSTOMER: {user_data['name']} (Phone: {phone_number})
                ADDRESS: {user_data['address']}, {user_data['city']}
                
                CURRENT MESSAGE: {message}
                {"(Voice message)" if is_voice_message else ""}
                
                INTENT:
                - Greeting: {is_greeting}
                - Confirming order: {is_confirmation}
                - Viewing order: {is_view_order}
                - Adding items: {is_adding_items}
                - Menu request: {is_menu_request}
                - Should show menu: {should_show_menu}
                
                RECENT CONVERSATION (Last 3):
                {self._get_recent_messages(conversation_history, limit=3)}
                
                INSTRUCTIONS: Respond immediately based on the detected intent. Be concise.
                """
                
                # Update state
                self.state_manager.update_user_state(phone_number, 'ordering')
                
                # Run restaurant agent with proper event loop handling
                response = self._run_agent_safely(
                    self.restaurant_agent,
                    context,
                    self.restaurant_config,
                    "Restaurant Agent"
                )
                
                # Ensure we have a response
                if not response or response.strip() == "":
                    print("⚠️ Empty response from agent, generating default response")
                    if is_greeting or is_new_session:
                        response = f"Hello {user_data.get('name', 'there')}! 👋 Welcome back to our restaurant! Let me show you our menu..."
                        # Force show menu
                        from tools.menu_tools import show_menu
                        menu_text = show_menu()
                        response = response + "\n\n" + menu_text
                    else:
                        response = "I'm here to help you with your order! You can:\n• Say 'menu' to see our offerings\n• Say 'view order' to check your cart\n• Tell me what you'd like to order!"
                
            else:
                # New user - use registration agent
                print(f"📝 Using Registration Agent for new user")
                
                # Send quick acknowledgment for new users
                try:
                    notification.answer("Welcome! I'll help you get registered. Just a moment... 🎯")
                except:
                    pass
                
                context = f"""
                NEW USER REGISTRATION
                Phone: {phone_number}
                
                RECENT CONVERSATION:
                {self._get_recent_messages(conversation_history, limit=5)}
                
                CURRENT MESSAGE: {message}
                {"(Voice message)" if is_voice_message else ""}
                
                Help this new user register by collecting their details.
                """
                
                # Update state
                self.state_manager.update_user_state(phone_number, 'registering')
                
                # Run registration agent with proper event loop handling
                response = self._run_agent_safely(
                    self.registration_agent,
                    context,
                    self.registration_config,
                    "Registration Agent"
                )
                
                # Check if registration was completed
                new_state = self.state_manager.get_user_state(phone_number)
                if new_state['is_registered'] and not user_exists:
                    # User just registered
                    print(f"✅ User registration completed! Showing menu...")
                    # Add menu immediately without running another agent
                    from tools.menu_tools import show_menu_base  # Import base function
                    menu_text = show_menu_base()  # Use base function
                    response = response + "\n\n" + menu_text
            
            # Save assistant response
            self.conversation_service.save_conversation(phone_number, "assistant", response)
            
            # Send response back to WhatsApp
            print(f"📤 Sending response to WhatsApp...")
            notification.answer(response)
            print(f"✅ Message handling completed successfully")
            
        except Exception as e:
            error_msg = f"Sorry, an error occurred: {str(e)}"
            print(f"❌ Error in message handler: {e}")
            import traceback
            traceback.print_exc()
            notification.answer(error_msg)
            if 'phone_number' in locals():
                self.conversation_service.save_conversation(phone_number, "assistant", error_msg)

    def _get_recent_messages(self, conversation_history, limit=3):
        """Get only recent messages for context"""
        messages = conversation_history.get('messages', [])
        recent = messages[-limit:] if len(messages) > limit else messages
        
        formatted = ""
        for msg in recent:
            role = "Customer" if msg["role"] == "user" else "Assistant"
            formatted += f"{role}: {msg['message']}\n"
        
        return formatted if formatted else "No recent messages"

    def _process_voice_message(self, notification: Notification, phone_number: str) -> Optional[str]:
        """Process voice message and convert to text"""
        try:
            print(f"🎤 Processing voice message from {phone_number}")
            
            # Get audio URL from notification
            audio_url = None
            
            # Check messageData using get_message_data()
            if hasattr(notification, 'get_message_data'):
                try:
                    message_data = notification.get_message_data()
                    if isinstance(message_data, dict):
                        print(f"📋 Searching for audio URL in message_data: {message_data}")
                        
                        # Check fileMessageData (common structure for files)
                        if 'fileMessageData' in message_data:
                            file_data = message_data['fileMessageData']
                            if isinstance(file_data, dict):
                                audio_url = file_data.get('downloadUrl')
                                if audio_url:
                                    print(f"📎 Found audio URL via get_message_data().fileMessageData.downloadUrl: {audio_url}")
                
                except Exception as e:
                    print(f"❌ Error accessing get_message_data(): {e}")
            
            if not audio_url:
                print("❌ No audio URL found in notification")
                return None
            
            print(f"🎤 Processing voice message from {phone_number}")
            print(f"🔗 Audio URL: {audio_url}")
            
            # Try to detect language from recent messages
            language = self._detect_language(phone_number)
            print(f"🌐 Detected language: {language}")
            
            # Convert voice to text using hybrid service
            try:
                text = self.speech_service.convert_voice_to_text(audio_url, language)
                
                if text and text.strip():
                    print(f"✅ Voice transcribed: {text}")
                    # Save with voice indicator
                    voice_indicator = "[🎤 Voice Message] " if language == "en" else "[🎤 صوتی پیغام] "
                    self.conversation_service.save_conversation(
                        phone_number,
                        "user",
                        f"{voice_indicator}{text}",
                        metadata={
                            "type": "voice",
                            "original_url": audio_url,
                            "detected_language": language
                        }
                    )
                    return text.strip()
                else:
                    print("❌ Failed to transcribe voice message - empty result")
                    return None
            except Exception as speech_error:
                print(f"❌ Speech service error: {speech_error}")
                return None
                
        except Exception as e:
            print(f"❌ Error processing voice message: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _detect_language(self, phone_number: str) -> str:
        """Simple language detection based on recent messages"""
        try:
            # Get recent conversation
            history = self.conversation_service.get_conversation_history(phone_number, limit=10)
            messages = history.get('messages', [])
            
            # Count Urdu characters in recent messages
            urdu_count = 0
            english_count = 0
            total_chars = 0
            
            for msg in messages:
                if msg['role'] == 'user':
                    text = msg['message']
                    # Remove voice message indicators
                    text = text.replace('[🎤 Voice Message] ', '').replace('[🎤 صوتی پیغام] ', '')
                    
                    # Count characters
                    for char in text:
                        if '\u0600' <= char <= '\u06FF':  # Arabic/Urdu script range
                            urdu_count += 1
                        elif 'a' <= char.lower() <= 'z':  # English characters
                            english_count += 1
                    
                    total_chars += len(text)
            
            # Determine language based on character count
            if total_chars > 0:
                urdu_percentage = urdu_count / total_chars
                english_percentage = english_count / total_chars
                
                print(f"Language detection - Urdu: {urdu_percentage:.2%}, English: {english_percentage:.2%}")
                
                # If more than 20% Urdu characters, assume Urdu
                if urdu_percentage > 0.2:
                    return 'ur'
                # If mostly English
                elif english_percentage > 0.5:
                    return 'en'
            
            # Default to English
            return 'en'
            
        except Exception as e:
            print(f"Error in language detection: {str(e)}")
            return 'en'  # Default to English

    def run(self):
        """Run the WhatsApp bot"""
        print("🍕 Restaurant WhatsApp Bot is running...")
        print("Features enabled:")
        print("✅ Dual Agent System (Registration + Restaurant)")
        print("✅ Proactive Menu Display")
        print("✅ WhatsApp Formatting")
        print("✅ Smart Conversation Management")
        print("✅ FREE Voice Message Support (English & Urdu) - Hybrid Mode")
        print("\nAgents initialized:")
        print("1️⃣ Registration Agent - For new users")
        print("2️⃣ Restaurant Agent - For existing users (shows menu proactively)")
        print("🎤 Hybrid Speech Recognition - Online + Offline Support")
        print("   • Primary: Google Web Speech API (Free, Online)")
        print("   • Fallback: Vosk (Offline)")
        print("\nVoice Message Features:")
        print("   • Automatic language detection (English/Urdu)")
        print("   • Multiple language fallbacks")
        print("   • Works without API keys")
        print("\n✅ Event loop handling configured for multi-threaded execution")
        
        self.bot.run_forever()

    def __del__(self):
        """Cleanup thread pool on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
