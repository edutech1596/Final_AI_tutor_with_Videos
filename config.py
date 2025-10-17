"""
Configuration file for AI Math Tutor
Loads configuration from environment variables for security
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# OpenAI API Configuration
# ============================================
# Load API key from environment variable (REQUIRED)
# Set in .env file or export OPENAI_API_KEY='your-key-here'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Validate that API key is set
if not OPENAI_API_KEY:
    raise ValueError(
        "❌ ERROR: OPENAI_API_KEY not found!\n"
        "Please set your OpenAI API key:\n"
        "1. Copy .env.example to .env\n"
        "2. Add your API key to .env file\n"
        "3. Or export OPENAI_API_KEY='your-key-here'"
    )

# OpenAI Model Selection
OPENAI_MODEL = "gpt-4o-mini"  # or "gpt-3.5-turbo" for faster/cheaper responses
OPENAI_TEMPERATURE = 0.3
OPENAI_MAX_TOKENS = 700  # Increased for complete answers (was 300)

# ============================================
# TTS Configuration (Piper)
# ============================================
# Path to Piper executable (download from: https://github.com/rhasspy/piper)
# Using gTTS (Google TTS) for high-quality natural voice
PIPER_EXECUTABLE = "./piper/piper"  # Piper binary (Linux only)
USE_PYTTSX3 = False  # Use Python TTS (robotic quality)
USE_GTTS = True  # Use Google TTS (high quality, requires internet)

# Path to Piper voice model
# Download models from: https://huggingface.co/rhasspy/piper-voices
PIPER_VOICE_MODEL = "./models/en_US-lessac-medium.onnx"

# Audio output settings
TTS_OUTPUT_DIR = "./audio_output"
TTS_SAMPLE_RATE = 22050

# ============================================
# STT Configuration
# ============================================
# Primary: Google Speech Recognition (high accuracy, requires internet)
USE_GOOGLE_STT = True  # ✅ High accuracy, free, requires internet

# Fallback: Vosk (offline, good accuracy)
# Path to Vosk model (download from: https://alphacephei.com/vosk/models)
VOSK_MODEL_PATH = "./models/vosk-model-small-en-us-0.15"  # ✅ Downloaded and ready!

# Audio input settings
STT_SAMPLE_RATE = 16000
STT_CHANNELS = 1
STT_RECORDING_DURATION = 10  # seconds to record when button pressed (increased for longer questions)

# ============================================
# Video Catalog Configuration
# ============================================
VIDEO_METADATA = {
    "Area_Circle": {
        "title": "Area of a Circle (Introduction to Pi)",
        "topic": "Geometry",
        "difficulty": "beginner",
        "duration": 180,  # seconds
        "video_path": "../manim_with_voice/media/videos/01_hello_manim_voice/480p15/HelloManimVoice.mp4"
    },
    "PythagoreanTheorem": {
        "title": "Derivation and Proof of the Pythagorean Theorem",
        "topic": "Geometry",
        "difficulty": "intermediate",
        "duration": 240,
        "video_path": ""
    },
    "QuadraticFormula": {
        "title": "Solving Quadratic Equations using the Formula",
        "topic": "Algebra",
        "difficulty": "intermediate",
        "duration": 300,
        "video_path": ""
    }
}

# ============================================
# System Tutor Prompt
# ============================================
SYSTEM_PROMPT = """You are an AI Math Tutor helping students understand mathematical concepts. 
Your role is to:
1. Answer questions clearly and concisely
2. Relate answers to the specific video topic the student is watching
3. Use simple language appropriate for the student's level
4. Provide examples when helpful
5. Encourage the student to continue learning

Keep responses under 100 words for voice delivery."""

