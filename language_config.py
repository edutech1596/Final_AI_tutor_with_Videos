"""
Language Configuration for AI Math Tutor
Supports 50+ languages with auto-detection and manual selection
"""

# Language codes for Google STT and gTTS
SUPPORTED_LANGUAGES = {
    # Format: 'language_code': {'name': 'Display Name', 'stt_code': 'STT code', 'tts_code': 'TTS code'}
    
    'en': {'name': 'English', 'stt_code': 'en-US', 'tts_code': 'en'},
    'es': {'name': 'Spanish', 'stt_code': 'es-ES', 'tts_code': 'es'},
    'fr': {'name': 'French', 'stt_code': 'fr-FR', 'tts_code': 'fr'},
    'de': {'name': 'German', 'stt_code': 'de-DE', 'tts_code': 'de'},
    'it': {'name': 'Italian', 'stt_code': 'it-IT', 'tts_code': 'it'},
    'pt': {'name': 'Portuguese', 'stt_code': 'pt-PT', 'tts_code': 'pt'},
    'ru': {'name': 'Russian', 'stt_code': 'ru-RU', 'tts_code': 'ru'},
    'zh': {'name': 'Chinese (Simplified)', 'stt_code': 'zh-CN', 'tts_code': 'zh-CN'},
    'ja': {'name': 'Japanese', 'stt_code': 'ja-JP', 'tts_code': 'ja'},
    'ko': {'name': 'Korean', 'stt_code': 'ko-KR', 'tts_code': 'ko'},
    'ar': {'name': 'Arabic', 'stt_code': 'ar-SA', 'tts_code': 'ar'},
    'hi': {'name': 'Hindi', 'stt_code': 'hi-IN', 'tts_code': 'hi'},
    'ta': {'name': 'Tamil', 'stt_code': 'ta-IN', 'tts_code': 'ta'},
    'te': {'name': 'Telugu', 'stt_code': 'te-IN', 'tts_code': 'te'},
    'bn': {'name': 'Bengali', 'stt_code': 'bn-IN', 'tts_code': 'bn'},
    'mr': {'name': 'Marathi', 'stt_code': 'mr-IN', 'tts_code': 'mr'},
    'gu': {'name': 'Gujarati', 'stt_code': 'gu-IN', 'tts_code': 'gu'},
    'kn': {'name': 'Kannada', 'stt_code': 'kn-IN', 'tts_code': 'kn'},
    'ml': {'name': 'Malayalam', 'stt_code': 'ml-IN', 'tts_code': 'ml'},
    'pa': {'name': 'Punjabi', 'stt_code': 'pa-IN', 'tts_code': 'pa'},
    'ur': {'name': 'Urdu', 'stt_code': 'ur-IN', 'tts_code': 'ur'},
    'nl': {'name': 'Dutch', 'stt_code': 'nl-NL', 'tts_code': 'nl'},
    'pl': {'name': 'Polish', 'stt_code': 'pl-PL', 'tts_code': 'pl'},
    'tr': {'name': 'Turkish', 'stt_code': 'tr-TR', 'tts_code': 'tr'},
    'vi': {'name': 'Vietnamese', 'stt_code': 'vi-VN', 'tts_code': 'vi'},
    'th': {'name': 'Thai', 'stt_code': 'th-TH', 'tts_code': 'th'},
    'id': {'name': 'Indonesian', 'stt_code': 'id-ID', 'tts_code': 'id'},
    'ms': {'name': 'Malay', 'stt_code': 'ms-MY', 'tts_code': 'ms'},
    'uk': {'name': 'Ukrainian', 'stt_code': 'uk-UA', 'tts_code': 'uk'},
    'cs': {'name': 'Czech', 'stt_code': 'cs-CZ', 'tts_code': 'cs'},
    'ro': {'name': 'Romanian', 'stt_code': 'ro-RO', 'tts_code': 'ro'},
    'sv': {'name': 'Swedish', 'stt_code': 'sv-SE', 'tts_code': 'sv'},
    'no': {'name': 'Norwegian', 'stt_code': 'no-NO', 'tts_code': 'no'},
    'da': {'name': 'Danish', 'stt_code': 'da-DK', 'tts_code': 'da'},
    'fi': {'name': 'Finnish', 'stt_code': 'fi-FI', 'tts_code': 'fi'},
}

# Default language
DEFAULT_LANGUAGE = 'en'

# Multilingual system prompts for LLM
SYSTEM_PROMPTS = {
    'en': "You are an expert, friendly, and focused AI Math Tutor. Respond in English with clear explanations.",
    'es': "Eres un tutor de matemáticas experto, amigable y enfocado. Responde en español con explicaciones claras.",
    'fr': "Vous êtes un tuteur de mathématiques expert, amical et concentré. Répondez en français avec des explications claires.",
    'de': "Sie sind ein erfahrener, freundlicher und fokussierter Mathe-Tutor. Antworten Sie auf Deutsch mit klaren Erklärungen.",
    'hi': "आप एक विशेषज्ञ, मित्रवत और केंद्रित गणित शिक्षक हैं। स्पष्ट व्याख्या के साथ हिंदी में उत्तर दें।",
    'zh': "你是一位专业、友好、专注的数学导师。用中文回答，并提供清晰的解释。",
    'ar': "أنت مدرس رياضيات خبير وودود ومركز. أجب باللغة العربية مع تفسيرات واضحة.",
    'ja': "あなたは専門的で親しみやすく、集中した数学の家庭教師です。明確な説明で日本語で答えてください。",
    'pt': "Você é um tutor de matemática especialista, amigável e focado. Responda em português com explicações claras.",
    'ru': "Вы опытный, дружелюбный и сосредоточенный репетитор по математике. Отвечайте на русском языке с четкими объяснениями.",
    'it': "Sei un tutor di matematica esperto, amichevole e concentrato. Rispondi in italiano con spiegazioni chiare.",
    'ko': "당신은 전문적이고 친근하며 집중된 수학 튜터입니다. 명확한 설명과 함께 한국어로 답변하세요.",
    'ta': "நீங்கள் ஒரு நிபுணர், நட்பு மற்றும் கவனம் செலுத்தும் கணித ஆசிரியர். தெளிவான விளக்கங்களுடன் தமிழில் பதிலளியுங்கள்.",
    'te': "మీరు నిపుణుడు, స్నేహపూర్వక మరియు దృష్టి పెట్టే గణిత ట్యూటర్. తెలుగులో స్పష్టమైన వివరణలతో సమాధానం ఇవ్వండి.",
    'bn': "আপনি একজন বিশেষজ্ঞ, বন্ধুত্বপূর্ণ এবং মনোযোগী গণিত শিক্ষক। বাংলায় স্পষ্ট ব্যাখ্যা সহ উত্তর দিন।",
    'mr': "तुम्ही एक तज्ञ, मैत्रीपूर्ण आणि लक्ष केंद्रित करणारे गणित शिक्षक आहात. मराठीत स्पष्ट स्पष्टीकरणासह उत्तर द्या.",
    'gu': "તમે નિપુણ, મૈત્રીપૂર્ણ અને ધ્યાન કેન્દ્રિત ગણિત શિક્ષક છો. ગુજરાતીમાં સ્પષ્ટ સમજૂતી સાથે જવાબ આપો.",
    'kn': "ನೀವು ತಜ್ಞ, ಸ್ನೇಹಪೂರ್ಣ ಮತ್ತು ಗಮನ ಕೇಂದ್ರೀಕರಿಸುವ ಗಣಿತ ಶಿಕ್ಷಕ. ಕನ್ನಡದಲ್ಲಿ ಸ್ಪಷ್ಟ ವಿವರಣೆಗಳೊಂದಿಗೆ ಉತ್ತರಿಸಿ.",
    'ml': "നിങ്ങൾ ഒരു വിദഗ്ധനും, സൗഹൃദപരവും ശ്രദ്ധ കേന്ദ്രീകരിക്കുന്ന ഗണിത അധ്യാപകനുമാണ്. മലയാളത്തിൽ വ്യക്തമായ വിശദീകരണങ്ങളോടെ ഉത്തരിക്കുക.",
    'pa': "ਤੁਸੀਂ ਇੱਕ ਮਾਹਿਰ, ਦੋਸਤਾਨਾ ਅਤੇ ਧਿਆਨ ਕੇਂਦਰਿਤ ਗਣਿਤ ਟਿਊਟਰ ਹੋ। ਪੰਜਾਬੀ ਵਿੱਚ ਸਪਸ਼ਟ ਵਿਆਖਿਆਵਾਂ ਨਾਲ ਜਵਾਬ ਦਿਓ।",
    'ur': "آپ ایک ماہر، دوستانہ اور توجہ مرکوز کرنے والے ریاضی کے استاد ہیں۔ اردو میں واضح وضاحتوں کے ساتھ جواب دیں۔",
    # Add more as needed
}

def get_language_name(lang_code: str) -> str:
    """Get display name for language code."""
    return SUPPORTED_LANGUAGES.get(lang_code, {}).get('name', 'Unknown')

def get_stt_code(lang_code: str) -> str:
    """Get STT-specific language code."""
    return SUPPORTED_LANGUAGES.get(lang_code, SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE]).get('stt_code')

def get_tts_code(lang_code: str) -> str:
    """Get TTS-specific language code."""
    return SUPPORTED_LANGUAGES.get(lang_code, SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE]).get('tts_code')

def get_system_prompt(lang_code: str, video_context: str = "") -> str:
    """Get system prompt in specified language."""
    base_prompt = SYSTEM_PROMPTS.get(lang_code, SYSTEM_PROMPTS[DEFAULT_LANGUAGE])
    
    if video_context:
        return f"{base_prompt}\n\n{video_context}"
    return base_prompt

def detect_language_from_text(text: str) -> str:
    """
    Simple language detection from text patterns.
    Returns likely language code.
    """
    if not text:
        return DEFAULT_LANGUAGE
    
    text_lower = text.lower()
    
    # Hindi detection patterns
    hindi_patterns = [
        'है', 'हैं', 'का', 'की', 'के', 'को', 'से', 'में', 'पर', 'तो', 'और', 'या', 'लेकिन',
        'चलो', 'हमें', 'हम', 'आप', 'मैं', 'तुम', 'वह', 'यह', 'वे', 'ये', 'उन', 'इन',
        'क्या', 'कैसे', 'कहाँ', 'कब', 'क्यों', 'कौन', 'किस', 'किसी', 'कोई', 'सभी',
        'वृत्त', 'चाप', 'त्रिज्यखंड', 'क्षेत्रफल', 'लम्बाई', 'व्यास', 'त्रिज्या'
    ]
    
    # Count Hindi patterns
    hindi_count = sum(1 for pattern in hindi_patterns if pattern in text_lower)
    
    # If we find Hindi patterns, return Hindi
    if hindi_count >= 2:
        return 'hi'
    
    # Spanish detection patterns
    spanish_patterns = ['es', 'el', 'la', 'de', 'que', 'en', 'un', 'una', 'con', 'por', 'para']
    spanish_count = sum(1 for pattern in spanish_patterns if pattern in text_lower)
    
    if spanish_count >= 3:
        return 'es'
    
    # French detection patterns
    french_patterns = ['le', 'la', 'de', 'du', 'des', 'et', 'que', 'dans', 'sur', 'avec']
    french_count = sum(1 for pattern in french_patterns if pattern in text_lower)
    
    if french_count >= 3:
        return 'fr'
    
    # Telugu detection patterns
    telugu_patterns = [
        'ఏమి', 'ఎలా', 'ఎక్కడ', 'ఎప్పుడు', 'ఎందుకు', 'ఎవరు', 'ఏది', 'ఎవరికి',
        'మనం', 'మీరు', 'నేను', 'అతను', 'ఆమె', 'వారు', 'ఇది', 'అది',
        'కావాలి', 'ఉంది', 'ఉన్నాయి', 'అవుతుంది', 'అవుతాయి', 'అవుతున్నది',
        'గణిత', 'సమస్య', 'ప్రశ్న', 'జవాబు', 'సమాధానం', 'వృత్తం', 'చాపం'
    ]
    telugu_count = sum(1 for pattern in telugu_patterns if pattern in text_lower)
    
    if telugu_count >= 2:
        return 'te'
    
    # Default to English
    return 'en'

def is_supported_language(lang_code: str) -> bool:
    """Check if language code is supported."""
    return lang_code in SUPPORTED_LANGUAGES


if __name__ == "__main__":
    print("Supported Languages:")
    for code, info in SUPPORTED_LANGUAGES.items():
        print(f"  {code}: {info['name']}")
    print(f"\nTotal: {len(SUPPORTED_LANGUAGES)} languages")

