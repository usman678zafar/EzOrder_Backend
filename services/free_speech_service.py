import os
import tempfile
import requests
from typing import Optional, List
import speech_recognition as sr
from pydub import AudioSegment
import json

class FreeSpeechToTextService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Configure recognizer for better accuracy
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        
    def convert_voice_to_text(self, audio_url: str, language: str = "en") -> Optional[str]:
        """
        Convert voice message to text using free Google Web Speech API
        
        Args:
            audio_url: URL of the voice message
            language: Language code ('en' for English, 'ur' for Urdu)
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Download audio file
            print(f"📥 Downloading audio from: {audio_url}")
            audio_data = self._download_audio(audio_url)
            if not audio_data:
                return None
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name
            
            # Convert to WAV format (required for speech recognition)
            wav_path = self._convert_to_wav(temp_audio_path)
            
            # Load audio file
            with sr.AudioFile(wav_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                
                # Record audio
                audio = self.recognizer.record(source)
            
            # Convert language code
            primary_lang = "en-US" if language == "en" else "ur-PK"
            
            print(f"🎤 Converting speech to text (Primary language: {primary_lang})...")
            
            # Try multiple recognition approaches
            text = self._recognize_with_fallback(audio, primary_lang)
            
            if text:
                print(f"✅ Transcribed text: {text}")
                return text
            else:
                print("❌ Could not understand audio in any language")
                return None
            
        except Exception as e:
            print(f"❌ Error in speech-to-text conversion: {str(e)}")
            return None
        finally:
            # Clean up temporary files
            if 'temp_audio_path' in locals():
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
            if 'wav_path' in locals():
                try:
                    os.unlink(wav_path)
                except:
                    pass
    
    def _recognize_with_fallback(self, audio, primary_language: str) -> Optional[str]:
        """
        Try to recognize speech with multiple language fallbacks
        
        Args:
            audio: Audio data
            primary_language: Primary language to try first
            
        Returns:
            Transcribed text or None
        """
        # Define language fallback order
        language_fallback_order = {
            "ur-PK": ["ur-PK", "hi-IN", "en-US", "en-IN"],  # Urdu → Hindi → English
            "en-US": ["en-US", "en-IN", "ur-PK", "hi-IN"],  # English → Urdu → Hindi
            "hi-IN": ["hi-IN", "ur-PK", "en-IN", "en-US"],  # Hindi → Urdu → English
        }
        
        # Get fallback languages
        languages_to_try = language_fallback_order.get(primary_language, [primary_language, "en-US"])
        
        # Try each language
        for lang_code in languages_to_try:
            try:
                print(f"🔍 Trying language: {lang_code}")
                text = self.recognizer.recognize_google(audio, language=lang_code)
                
                if text and text.strip():
                    print(f"✅ Successfully recognized with {lang_code}")
                    # If we used a fallback language, indicate it
                    if lang_code != primary_language:
                        return f"{text} [Auto-detected: {self._get_language_name(lang_code)}]"
                    return text
                    
            except sr.UnknownValueError:
                print(f"❌ Could not understand audio in {lang_code}")
                continue
            except sr.RequestError as e:
                print(f"❌ Error with Google Speech Recognition for {lang_code}: {e}")
                continue
            except Exception as e:
                print(f"❌ Unexpected error with {lang_code}: {e}")
                continue
        
        # If all languages fail, try without specifying language (auto-detect)
        try:
            print("🔍 Trying auto-detection...")
            text = self.recognizer.recognize_google(audio)
            if text and text.strip():
                print("✅ Successfully recognized with auto-detection")
                return f"{text} [Auto-detected]"
        except:
            pass
        
        return None
    
    def _get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name"""
        language_names = {
            "en-US": "English",
            "en-IN": "Indian English",
            "ur-PK": "Urdu",
            "hi-IN": "Hindi"
        }
        return language_names.get(lang_code, lang_code)
    
    def _download_audio(self, audio_url: str) -> Optional[bytes]:
        """Download audio file from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(audio_url, headers=headers, timeout=30)
            if response.status_code == 200:
                print(f"✅ Audio downloaded successfully ({len(response.content)} bytes)")
                return response.content
            else:
                print(f"❌ Failed to download audio: Status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading audio: {str(e)}")
            return None
    
    def _convert_to_wav(self, audio_path: str) -> str:
        """Convert audio to WAV format with optimal settings for speech recognition"""
        try:
            # Load audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Convert to optimal format for speech recognition
            # - Mono channel
            # - 16kHz sample rate (optimal for speech)
            # - 16-bit depth
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Apply noise reduction if audio is too quiet
            if audio.dBFS < -30:
                audio = audio + 10  # Increase volume by 10dB
            
            # Save as WAV
            wav_path = audio_path.replace('.ogg', '.wav')
            audio.export(wav_path, format="wav")
            
            print(f"✅ Audio converted to WAV format (16kHz, mono)")
            return wav_path
            
        except Exception as e:
            print(f"❌ Error converting audio: {str(e)}")
            raise


# Alternative implementation using Vosk for completely offline support
class VoskSpeechToTextService:
    def __init__(self):
        # Import vosk only if being used
        try:
            import vosk
            self.vosk = vosk
        except ImportError:
            print("❌ Vosk not installed. Run: pip install vosk")
            self.vosk = None
            
        # Setup models
        self.models = {}
        if self.vosk:
            self.models = {
                'en': self._setup_model('en'),
                'ur': self._setup_model('ur'),
                'hi': self._setup_model('hi')  # Hindi as fallback for Urdu
            }
    
    def _setup_model(self, language: str):
        """Setup Vosk model for language"""
        if not self.vosk:
            return None
            
        model_info = {
            'en': {
                'path': 'vosk-model-small-en-us-0.15',
                'url': 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip',
                'size': '40MB'
            },
            'ur': {
                'path': 'vosk-model-small-ur-0.22',
                'url': 'https://alphacephei.com/vosk/models/vosk-model-small-ur-0.22.zip',
                'size': '40MB'
            },
            'hi': {
                'path': 'vosk-model-small-hi-0.22',
                'url': 'https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip',
                'size': '42MB'
            }
        }
        
        info = model_info.get(language)
        if not info:
            return None
        
        model_path = info['path']
        
        # Check if model exists
        if not os.path.exists(model_path):
            print(f"📥 {language.upper()} model not found.")
            print(f"Please download from: {info['url']} ({info['size']})")
            print(f"Extract to: {model_path}")
            
            # Try to auto-download if possible
            self._try_download_model(info['url'], model_path)
            
            if not os.path.exists(model_path):
                return None
        
        try:
            print(f"✅ Loading {language.upper()} model...")
            return self.vosk.Model(model_path)
        except Exception as e:
            print(f"❌ Failed to load {language} model: {e}")
            return None
    
    def _try_download_model(self, url: str, path: str):
        """Try to automatically download and extract model"""
        try:
            print(f"🔄 Attempting to download model...")
            import zipfile
            import io
            
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                # Download and extract
                z = zipfile.ZipFile(io.BytesIO(response.content))
                z.extractall('.')
                print(f"✅ Model downloaded and extracted")
            else:
                print(f"❌ Failed to download model")
        except Exception as e:
            print(f"❌ Auto-download failed: {e}")
            print("Please download manually")
    
    def convert_voice_to_text(self, audio_url: str, language: str = "en") -> Optional[str]:
        """Convert voice to text using Vosk (offline)"""
        if not self.vosk:
            print("❌ Vosk not available")
            return None
            
        # Try primary language and fallbacks
        languages_to_try = []
        if language == "ur":
            languages_to_try = ["ur", "hi", "en"]  # Urdu → Hindi → English
        else:
            languages_to_try = [language, "en"]  # Primary → English
        
        for lang in languages_to_try:
            model = self.models.get(lang)
            if model:
                result = self._recognize_with_model(audio_url, model, lang)
                if result:
                    if lang != language:
                        return f"{result} [Fallback: {lang.upper()}]"
                    return result
        
        return None
    
    def _recognize_with_model(self, audio_url: str, model, language: str) -> Optional[str]:
        """Recognize speech using specific Vosk model"""
        try:
            # Download audio
            audio_data = self._download_audio(audio_url)
            if not audio_data:
                return None
            
            # Save and convert to WAV
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_audio:
                temp_audio.write(audio_data)
                temp_audio_path = temp_audio.name
            
            # Convert to 16kHz mono WAV
            audio = AudioSegment.from_file(temp_audio_path)
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            
            wav_path = temp_audio_path.replace('.ogg', '.wav')
            audio.export(wav_path, format="wav", parameters=["-ac", "1"])
            
            # Recognize with Vosk
            rec = self.vosk.KaldiRecognizer(model, 16000)
            rec.SetWords(True)  # Enable word-level recognition
            
            results = []
            with open(wav_path, 'rb') as wf:
                while True:
                    data = wf.read(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        if result.get('text'):
                            results.append(result['text'])
                
                # Get final result
                final_result = json.loads(rec.FinalResult())
                if final_result.get('text'):
                    results.append(final_result['text'])
            
            # Clean up
            os.unlink(temp_audio_path)
            os.unlink(wav_path)
            
            # Combine all text
            text = ' '.join(results)
            return text.strip() if text else None
            
        except Exception as e:
            print(f"❌ Error in Vosk recognition ({language}): {str(e)}")
            return None
    
    def _download_audio(self, audio_url: str) -> Optional[bytes]:
        """Download audio file"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(audio_url, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.content
            return None
        except:
            return None


# Hybrid service that tries online first, then offline
class HybridSpeechToTextService:
    def __init__(self):
        self.online_service = FreeSpeechToTextService()
        self.offline_service = VoskSpeechToTextService()
        
    def convert_voice_to_text(self, audio_url: str, language: str = "en") -> Optional[str]:
        """Try online service first, fallback to offline if needed"""
        # Try online first (better accuracy)
        print("🌐 Trying online speech recognition...")
        result = self.online_service.convert_voice_to_text(audio_url, language)
        
        if result:
            return result
        
        # Fallback to offline
        if self.offline_service.vosk:
            print("💾 Trying offline speech recognition...")
            result = self.offline_service.convert_voice_to_text(audio_url, language)
            if result:
                return f"{result} [Offline]"
        
        return None
