"""
Audio Utilities for STT and TTS Integration

Helper functions to:
- Decode Base64 audio from frontend
- Save to temporary file
- Transcribe using Google Speech Recognition
- Clean up temporary files
"""

import base64
import tempfile
import os
import speech_recognition as sr
from pydub import AudioSegment
from language_config import get_stt_code, DEFAULT_LANGUAGE


def decode_and_transcribe_audio(audio_base64: str, language: str = None) -> tuple[str, str]:
    """
    Decode Base64 audio and transcribe using Google Speech Recognition.
    Handles WebM/Opus format from browser and converts to WAV.
    Supports auto-detection or manual language selection.
    
    Args:
        audio_base64: Base64-encoded audio data (WebM/Opus from browser)
        language: Language code (e.g., 'en', 'es', 'fr'). If None, auto-detects.
        
    Returns:
        Tuple of (transcribed_text, detected_language_code)
    """
    print("[Audio Utils] Decoding audio from Base64...")
    print(f"[Audio Utils] Language preference: {language or 'auto-detect'}")
    
    temp_webm_path = None
    temp_wav_path = None
    
    try:
        # Decode Base64 to bytes
        audio_bytes = base64.b64decode(audio_base64)
        print(f"[Audio Utils] Decoded {len(audio_bytes)} bytes")
        print(f"[Audio Utils] First 20 bytes (hex): {audio_bytes[:20].hex()}")
        
        # Detect format from magic bytes
        if audio_bytes[:4] == b'RIFF':
            file_format = 'wav'
            suffix = '.wav'
            print("[Audio Utils] Detected format: WAV")
        elif audio_bytes[:4] == b'\x1a\x45\xdf\xa3':
            file_format = 'webm'
            suffix = '.webm'
            print("[Audio Utils] Detected format: WebM")
        elif b'ftyp' in audio_bytes[:12]:
            # MP4/M4A format (Safari uses this)
            file_format = 'mp4'
            suffix = '.m4a'
            print("[Audio Utils] Detected format: MP4/M4A (Safari)")
        elif audio_bytes[:3] == b'ID3' or audio_bytes[:2] == b'\xff\xfb':
            file_format = 'mp3'
            suffix = '.mp3'
            print("[Audio Utils] Detected format: MP3")
        else:
            print(f"[Audio Utils] ⚠️  Unknown format (hex: {audio_bytes[:20].hex()})")
            print(f"[Audio Utils] Trying to decode without format specification...")
            file_format = None  # Let pydub auto-detect
            suffix = '.audio'
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_webm_path = temp_file.name
        
        print(f"[Audio Utils] Saved to: {temp_webm_path}")
        
        # If already WAV, skip conversion
        if file_format == 'wav':
            temp_wav_path = temp_webm_path
            print("[Audio Utils] Already WAV format, skipping conversion")
        else:
            # Convert to WAV using pydub
            print(f"[Audio Utils] Converting {file_format or 'unknown'} to WAV...")
            if file_format:
                audio = AudioSegment.from_file(temp_webm_path, format=file_format)
            else:
                # Auto-detect format
                audio = AudioSegment.from_file(temp_webm_path)
        
            # Export as WAV (mono, 16kHz for better speech recognition)
            temp_wav_path = temp_webm_path.replace(suffix, '.wav')
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_frame_rate(16000)  # 16kHz sample rate
            audio.export(temp_wav_path, format="wav")
            
            print(f"[Audio Utils] Converted to WAV: {temp_wav_path}")
        
        # Transcribe using Google Speech Recognition
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(temp_wav_path) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            
            # Record audio
            audio_data = recognizer.record(source)
            
            # Transcribe with language support
            print("[Audio Utils] Transcribing with Google Speech Recognition...")
            
            detected_lang = language or DEFAULT_LANGUAGE
            
            if language:
                # Use specified language
                stt_lang_code = get_stt_code(language)
                print(f"[Audio Utils] Using specified language: {language} ({stt_lang_code})")
                text = recognizer.recognize_google(audio_data, language=stt_lang_code)
            else:
                # Auto-detect: Try with show_all to get confidence scores
                print("[Audio Utils] Auto-detecting language...")
                try:
                    # Try English first as default
                    text = recognizer.recognize_google(audio_data, language='en-US')
                    detected_lang = 'en'
                except sr.UnknownValueError:
                    # If English fails, try with auto-detect (no language specified)
                    text = recognizer.recognize_google(audio_data)
                    detected_lang = DEFAULT_LANGUAGE
            
            print(f"[Audio Utils] ✅ Transcription: '{text}'")
            print(f"[Audio Utils] ✅ Detected/Used Language: {detected_lang}")
            
            return text, detected_lang
    
    except sr.UnknownValueError:
        print("[Audio Utils] ❌ Could not understand audio - please speak more clearly")
        return "", language or DEFAULT_LANGUAGE
    
    except sr.RequestError as e:
        print(f"[Audio Utils] ❌ Google Speech Recognition error: {e}")
        return "", language or DEFAULT_LANGUAGE
    
    except Exception as e:
        print(f"[Audio Utils] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return "", language or DEFAULT_LANGUAGE
    
    finally:
        # Clean up temporary files
        for temp_file in [temp_webm_path, temp_wav_path]:
            try:
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"[Audio Utils] Cleaned up: {temp_file}")
            except Exception as e:
                print(f"[Audio Utils] Warning: Could not delete {temp_file}: {e}")


def transcribe_audio_file(filepath: str) -> str:
    """
    Transcribe an audio file using Google Speech Recognition.
    
    Args:
        filepath: Path to audio file
        
    Returns:
        Transcribed text
    """
    try:
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(filepath) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"Google Speech Recognition error: {e}")
        return ""
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return ""


# Test function
if __name__ == "__main__":
    print("Audio Utils Module Ready")
    print("Functions:")
    print("  - decode_and_transcribe_audio()")
    print("  - transcribe_audio_file()")
