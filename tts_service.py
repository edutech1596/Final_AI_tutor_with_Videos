"""
OPTIMIZED TTS Service: Text-to-Speech with caching and performance improvements
Supports multiple TTS engines with intelligent fallback and caching
"""

import os
import subprocess
import time
import hashlib
from pathlib import Path
from config import (
    PIPER_EXECUTABLE,
    PIPER_VOICE_MODEL,
    TTS_OUTPUT_DIR,
    TTS_SAMPLE_RATE,
    USE_PYTTSX3,
    USE_GTTS
)
from language_config import get_tts_code, DEFAULT_LANGUAGE
from cache_service import get_cached_tts_response, cache_tts_response
from llm_service import convert_formulas_to_spoken_words

# Try to import pyttsx3 (works on all platforms)
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# Try to import gTTS (requires internet)
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


def generate_audio_response(text: str, output_filename: str = None, language: str = None) -> str:
    """
    OPTIMIZED: Generates speech audio with caching and performance tracking.
    Priority: Cache > gTTS (best quality) > Piper > pyttsx3 > fallback
    Supports 50+ languages with intelligent caching!
    
    Args:
        text: The text to convert to speech.
        output_filename: Optional custom filename (without extension).
        language: Language code (e.g., 'en', 'es', 'fr'). Defaults to English.
        
    Returns:
        Path to the generated audio file.
    """
    import time
    start_time = time.time()
    
    lang = language or DEFAULT_LANGUAGE
    print("-" * 60)
    print(f"| OPTIMIZED TTS Service: Generating audio...")
    print(f"| Language: {lang}")
    print(f"| Text: '{text[:70]}...'")
    
    # ========================================================================
    # STEP 1: Check cache first
    # ========================================================================
    
    # Convert formulas to spoken words for TTS
    cleaned_text = convert_formulas_to_spoken_words(text)
    cached_audio = get_cached_tts_response(cleaned_text, lang)
    if cached_audio and os.path.exists(cached_audio):
        response_time = time.time() - start_time
        print(f"| 🎯 Cache HIT! Response time: {response_time:.2f}s")
        print(f"| File: {cached_audio}")
        print("-" * 60)
        return cached_audio
    
    # ========================================================================
    # STEP 2: Generate new audio with fallback chain
    # ========================================================================
    
    # Create output directory if it doesn't exist
    os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)
    
    # Generate filename
    if output_filename is None:
        timestamp = int(time.time())
        output_filename = f"tutor_response_{timestamp}"
    
    audio_filepath = os.path.join(TTS_OUTPUT_DIR, f"{output_filename}.wav")
    
    # Try TTS engines in order of preference
    success = False
    
    # Try gTTS FIRST (best quality, requires internet, multilingual)
    if USE_GTTS and GTTS_AVAILABLE and not success:
        try:
            success = _generate_with_gtts(text, audio_filepath, lang)
            if success:
                print(f"| ✅ Audio generated with gTTS (Google TTS - High Quality)")
        except Exception as e:
            print(f"| ⚠️  gTTS failed (internet required): {e}")
    
    # Try pyttsx3 as fallback (works offline but lower quality)
    if USE_PYTTSX3 and PYTTSX3_AVAILABLE and not success:
        try:
            success = _generate_with_pyttsx3(cleaned_text, audio_filepath)
            if success:
                print(f"| ✅ Audio generated with pyttsx3 (System TTS)")
        except Exception as e:
            print(f"| ⚠️  pyttsx3 failed: {e}")
    
    # Try Piper if available (Linux only)
    if _is_piper_available() and not success:
        try:
            success = _generate_with_piper(cleaned_text, audio_filepath)
            if success:
                print(f"| ✅ Audio generated with Piper TTS")
        except Exception as e:
            print(f"| ⚠️  Piper TTS failed: {e}")
    
    # Final fallback: Create a dummy audio file
    if not success:
        _generate_fallback_audio(text, audio_filepath)
        print(f"| ⚠️  Using FALLBACK (simulated audio)")
    
    # ========================================================================
    # STEP 3: Cache the result
    # ========================================================================
    
    if success:
        cache_tts_response(cleaned_text, audio_filepath, lang)
        print(f"| 💾 Cached for future use")
    
    response_time = time.time() - start_time
    print(f"| Language: {lang}")
    print(f"| File: {audio_filepath}")
    print(f"| Response time: {response_time:.2f}s")
    print("-" * 60)
    
    return audio_filepath


def _generate_with_pyttsx3(text: str, output_path: str) -> bool:
    """
    Generate audio using pyttsx3 (native Python TTS).
    Works on macOS, Windows, and Linux.
    """
    try:
        engine = pyttsx3.init()
        
        # Configure voice settings
        engine.setProperty('rate', 150)  # Speed (words per minute)
        engine.setProperty('volume', 0.9)  # Volume (0-1)
        
        # Optional: Set voice (get available voices)
        voices = engine.getProperty('voices')
        # Use first available voice (usually default system voice)
        if voices:
            engine.setProperty('voice', voices[0].id)
        
        # Save to file
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        
        # Check if file was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        return False
    except Exception as e:
        print(f"| pyttsx3 error: {e}")
        return False


def _generate_with_gtts(text: str, output_path: str, language: str = None) -> bool:
    """
    Generate audio using gTTS (Google TTS).
    Requires internet connection.
    Supports 50+ languages!
    """
    try:
        lang_code = get_tts_code(language or DEFAULT_LANGUAGE)
        print(f"| gTTS using language code: {lang_code}")
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
        # Save to mp3 first, then convert to wav if needed
        mp3_path = output_path.replace('.wav', '.mp3')
        tts.save(mp3_path)
        
        # If mp3 is requested, return
        if output_path.endswith('.mp3'):
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                return True
        
        # Convert mp3 to wav using pydub
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(mp3_path)
            audio.export(output_path, format="wav")
            os.remove(mp3_path)  # Clean up mp3 file
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
        except ImportError:
            # If pydub not available, just rename mp3 to wav
            os.rename(mp3_path, output_path)
            return True
        
        return False
    except Exception as e:
        print(f"| gTTS error: {e}")
        return False


def _is_piper_available() -> bool:
    """Check if Piper executable and model are available."""
    if not os.path.exists(PIPER_EXECUTABLE):
        return False
    if not os.path.exists(PIPER_VOICE_MODEL):
        return False
    return True


def _generate_with_piper(text: str, output_path: str) -> bool:
    """
    Generate audio using Piper TTS binary.
    
    Piper command format:
    echo "text" | piper --model model.onnx --output_file output.wav
    """
    try:
        # Prepare the command
        cmd = [
            PIPER_EXECUTABLE,
            "--model", PIPER_VOICE_MODEL,
            "--output_file", output_path
        ]
        
        # Run Piper with text input via stdin
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send text to Piper
        stdout, stderr = process.communicate(input=text)
        
        # Check if file was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            print(f"| Piper stderr: {stderr}")
            return False
            
    except Exception as e:
        print(f"| Exception in Piper execution: {e}")
        return False


def _generate_fallback_audio(text: str, output_path: str):
    """
    Generate a placeholder audio file for testing.
    This creates a valid WAV file header with silence.
    """
    import wave
    import struct
    
    # Create a simple silent WAV file
    duration = 2.0  # seconds
    sample_rate = TTS_SAMPLE_RATE
    num_samples = int(sample_rate * duration)
    
    with wave.open(output_path, 'w') as wav_file:
        # Set WAV file parameters
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Write silent frames
        for _ in range(num_samples):
            # Write silence (value 0)
            wav_file.writeframes(struct.pack('h', 0))
    
    # Also save metadata
    metadata_path = output_path.replace('.wav', '_metadata.txt')
    with open(metadata_path, 'w') as f:
        f.write(f"TTS TEXT: {text}\n")
        f.write(f"TIMESTAMP: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"NOTE: This is a simulated audio file. Install Piper for real TTS.\n")


def cleanup_old_audio_files(max_age_hours: int = 24):
    """
    Clean up old audio files to save disk space.
    
    Args:
        max_age_hours: Delete files older than this many hours.
    """
    if not os.path.exists(TTS_OUTPUT_DIR):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for filename in os.listdir(TTS_OUTPUT_DIR):
        filepath = os.path.join(TTS_OUTPUT_DIR, filename)
        if os.path.isfile(filepath):
            file_age = current_time - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                os.remove(filepath)
                print(f"Cleaned up old file: {filename}")


if __name__ == "__main__":
    # Test the TTS service
    print("=" * 60)
    print("Testing TTS Service")
    print("=" * 60)
    
    test_text = "Hello! This is a test of the text-to-speech system. The area of a circle is pi times radius squared."
    
    print("\n1. Checking Piper availability:")
    if _is_piper_available():
        print(f"   ✅ Piper executable found: {PIPER_EXECUTABLE}")
        print(f"   ✅ Voice model found: {PIPER_VOICE_MODEL}")
    else:
        print(f"   ⚠️  Piper not configured. Will use fallback.")
        print(f"   Expected executable: {PIPER_EXECUTABLE}")
        print(f"   Expected model: {PIPER_VOICE_MODEL}")
    
    print("\n2. Generating test audio:")
    audio_path = generate_audio_response(test_text, "test_audio")
    
    print(f"\n3. Result:")
    print(f"   Audio file: {audio_path}")
    print(f"   File size: {os.path.getsize(audio_path)} bytes")
    print(f"   File exists: {os.path.exists(audio_path)}")
    
    print("\n✅ TTS Service test complete!")
