"""
LLM Service: AI Tutor Brain with Real OpenAI Integration
Optimized with caching, error handling, and performance improvements
"""

import os
import asyncio
import aiohttp
from openai import OpenAI, AsyncOpenAI
from config import (
    OPENAI_API_KEY, 
    OPENAI_MODEL, 
    OPENAI_TEMPERATURE, 
    OPENAI_MAX_TOKENS,
    VIDEO_METADATA,
    SYSTEM_PROMPT
)
from conversation_logger import ConversationLogger
from session_manager import session_manager
from cache_service import get_cached_llm_response, cache_llm_response

# Initialize OpenAI clients (sync and async)
client = OpenAI(api_key=OPENAI_API_KEY)
async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Initialize conversation logger for revision and personalized learning
conversation_logger = ConversationLogger()

# Performance tracking
class PerformanceTracker:
    def __init__(self):
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "api_calls": 0,
            "avg_response_time": 0,
            "errors": 0
        }
    
    def record_request(self, response_time: float, from_cache: bool = False, error: bool = False):
        self.stats["total_requests"] += 1
        if from_cache:
            self.stats["cache_hits"] += 1
        else:
            self.stats["api_calls"] += 1
        if error:
            self.stats["errors"] += 1
        
        # Update average response time
        if not from_cache:
            current_avg = self.stats["avg_response_time"]
            total_calls = self.stats["api_calls"]
            self.stats["avg_response_time"] = ((current_avg * (total_calls - 1)) + response_time) / total_calls
    
    def get_stats(self):
        return self.stats.copy()

performance_tracker = PerformanceTracker()

def clean_markdown_for_tts(text: str) -> str:
    """
    Clean markdown and LaTeX formatting for TTS and display.
    Removes LaTeX commands, preserves ChatGPT-style formatting.
    """
    import re

    # ========================================================================
    # STEP 1: Clean LaTeX formatting (CRITICAL for TTS)
    # ========================================================================
    
    # Remove LaTeX display math blocks \[ ... \]
    text = re.sub(r'\\\[([\s\S]*?)\\\]', r'\1', text)
    
    # Remove LaTeX inline math \( ... \)
    text = re.sub(r'\\\(([\s\S]*?)\\\)', r'\1', text)
    
    # Clean common LaTeX commands
    text = re.sub(r'\\times', '×', text)  # \times -> ×
    text = re.sub(r'\\left', '', text)  # \left -> remove
    text = re.sub(r'\\right', '', text)  # \right -> remove
    text = re.sub(r'\\pi', 'π', text)  # \pi -> π
    text = re.sub(r'\\theta', 'θ', text)  # \theta -> θ
    text = re.sub(r'\\alpha', 'α', text)  # \alpha -> α
    text = re.sub(r'\\beta', 'β', text)  # \beta -> β
    text = re.sub(r'\\gamma', 'γ', text)  # \gamma -> γ
    text = re.sub(r'\\delta', 'δ', text)  # \delta -> δ
    text = re.sub(r'\\epsilon', 'ε', text)  # \epsilon -> ε
    text = re.sub(r'\\lambda', 'λ', text)  # \lambda -> λ
    text = re.sub(r'\\mu', 'μ', text)  # \mu -> μ
    text = re.sub(r'\\sigma', 'σ', text)  # \sigma -> σ
    text = re.sub(r'\\phi', 'φ', text)  # \phi -> φ
    text = re.sub(r'\\omega', 'ω', text)  # \omega -> ω
    
    # Clean LaTeX spacing commands (CRITICAL for TTS)
    text = re.sub(r'\\,', ' ', text)  # \thinspace -> space
    text = re.sub(r'\\:', ' ', text)  # \medspace -> space  
    text = re.sub(r'\\;', ' ', text)  # \thickspace -> space
    text = re.sub(r'\\!', '', text)   # \negthinspace -> remove
    text = re.sub(r'\\quad', ' ', text)  # \quad -> space
    text = re.sub(r'\\qquad', ' ', text)  # \qquad -> space
    
    # Clean LaTeX fractions
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', text)
    
    # Clean LaTeX superscripts and subscripts
    text = re.sub(r'\^(\d+)', r'^\1', text)  # Keep ^2, ^3, etc.
    text = re.sub(r'_(\d+)', r'_\1', text)  # Keep _1, _2, etc.
    
    # Clean LaTeX text commands
    text = re.sub(r'\\text\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\textbf\{([^}]+)\}', r'\1', text)
    text = re.sub(r'\\textit\{([^}]+)\}', r'\1', text)
    
    # ========================================================================
    # STEP 2: Clean markdown formatting
    # ========================================================================
    
    # Remove bold/italic markdown but keep content
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # *italic* -> italic
    text = re.sub(r'__(.*?)__', r'\1', text)       # __bold__ -> bold
    text = re.sub(r'_(.*?)_', r'\1', text)         # _italic_ -> italic
    
    # Remove code formatting
    text = re.sub(r'`([^`]+)`', r'\1', text)       # `code` -> code
    text = re.sub(r'```[\s\S]*?```', '', text)     # Remove code blocks
    
    # Remove markdown links
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # ========================================================================
    # STEP 3: Preserve ChatGPT-style formatting
    # ========================================================================
    
    # Keep step patterns with proper spacing
    text = re.sub(r"Step\s*(\d+):", r"\n\nStep \1:", text)  # English steps
    text = re.sub(r"चरण\s*(\d+):", r"\n\nचरण \1:", text)  # Hindi steps
    text = re.sub(r"Paso\s*(\d+):", r"\n\nPaso \1:", text)  # Spanish steps
    text = re.sub(r"Étape\s*(\d+):", r"\n\nÉtape \1:", text)  # French steps
    text = re.sub(r"Schritt\s*(\d+):", r"\n\nSchritt \1:", text)  # German steps
    text = re.sub(r"Passo\s*(\d+):", r"\n\nPasso \1:", text)  # Italian steps
    text = re.sub(r"ステップ\s*(\d+):", r"\n\nステップ \1:", text)  # Japanese steps
    text = re.sub(r"단계\s*(\d+):", r"\n\n단계 \1:", text)  # Korean steps
    text = re.sub(r"步骤\s*(\d+):", r"\n\n步骤 \1:", text)  # Chinese steps
    text = re.sub(r"خطوة\s*(\d+):", r"\n\nخطوة \1:", text)  # Arabic steps
    
    # Preserve bullet points
    text = re.sub(r"•\s*", "\n• ", text)  # Ensure bullet points are on new lines
    
    # Keep important formatting markers
    text = re.sub(r"Important:", "\n\nImportant:", text)
    text = re.sub(r"Answer:", "\n\nAnswer:", text)
    text = re.sub(r"Formula:", "\n\nFormula:", text)
    text = re.sub(r"Final Answer:", "\n\nFinal Answer:", text)
    
    # Preserve numbered lists
    text = re.sub(r"(\d+\.\s)", r"\n\n\1", text)  # Numbered lists like "1. ", "2. "
    text = re.sub(r"(\d+\)\s)", r"\n\n\1", text)  # Numbered lists like "1) ", "2) "
    
    # ========================================================================
    # STEP 4: Clean up formatting
    # ========================================================================
    
    # Remove headers
    text = re.sub(r"^#+\s*", "\n\n", text, flags=re.MULTILINE)
    
    # Clean up excessive spacing but preserve structure
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)  # Remove excessive line breaks
    text = re.sub(r"^\s+", "", text, flags=re.MULTILINE)  # Remove leading spaces
    
    # Clean up stray formatting characters
    text = re.sub(r"[`#]", "", text)
    
    return text.strip()


def convert_formulas_to_spoken_words(text: str) -> str:
    """
    Convert common math notation in a text answer to a TTS-friendly
    spoken form while preserving meaning. Intended ONLY for audio output.
    """
    import re

    if not text:
        return text

    # First, remove markdown wrappers but keep content
    t = clean_markdown_for_tts(text)

    # ========================================================================
    # STEP 1: Clean LaTeX commands (CRITICAL for TTS)
    # ========================================================================
    
    # Clean LaTeX math symbols
    t = t.replace("\\times", " times ")
    t = t.replace("\\left", "").replace("\\right", "")
    t = t.replace("\\frac", " divided by ")
    t = t.replace("\\pi", " pi ")
    t = t.replace("\\theta", " theta ")
    t = t.replace("\\alpha", " alpha ")
    t = t.replace("\\beta", " beta ")
    t = t.replace("\\gamma", " gamma ")
    t = t.replace("\\delta", " delta ")
    t = t.replace("\\epsilon", " epsilon ")
    t = t.replace("\\lambda", " lambda ")
    t = t.replace("\\mu", " mu ")
    t = t.replace("\\sigma", " sigma ")
    t = t.replace("\\phi", " phi ")
    t = t.replace("\\omega", " omega ")
    
    # Clean LaTeX spacing commands (CRITICAL for TTS)
    t = t.replace("\\,", " ")  # \thinspace -> space
    t = t.replace("\\:", " ")  # \medspace -> space  
    t = t.replace("\\;", " ")  # \thickspace -> space
    t = t.replace("\\!", "")   # \negthinspace -> remove
    t = t.replace("\\quad", " ")  # \quad -> space
    t = t.replace("\\qquad", " ")  # \qquad -> space
    
    # Clean LaTeX fractions: \frac{a}{b} -> a divided by b
    t = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1 divided by \2', t)
    
    # Clean LaTeX superscripts and subscripts
    t = re.sub(r'\^(\d+)', r' to the power of \1', t)
    t = re.sub(r'_(\d+)', r' subscript \1', t)
    
    # Clean LaTeX text commands
    t = re.sub(r'\\text\{([^}]+)\}', r'\1', t)
    t = re.sub(r'\\textbf\{([^}]+)\}', r'\1', t)
    t = re.sub(r'\\textit\{([^}]+)\}', r'\1', t)
    
    # Clean additional LaTeX commands that might appear in audio
    t = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', t)  # Remove any remaining LaTeX commands with braces
    t = re.sub(r'\\[a-zA-Z]+', '', t)  # Remove any remaining single LaTeX commands
    
    # Remove LaTeX math delimiters
    t = re.sub(r'\\\[([\s\S]*?)\\\]', r'\1', t)
    t = re.sub(r'\\\(([\s\S]*?)\\\)', r'\1', t)

    # Normalize unicode superscripts to caret form to simplify rules
    t = t.replace("²", "^2").replace("³", "^3")

    # Pi
    t = t.replace("π", "pi")
    
    # Greek letters
    t = t.replace("θ", "theta")
    t = t.replace("α", "alpha")
    t = t.replace("β", "beta")
    t = t.replace("γ", "gamma")
    t = t.replace("δ", "delta")
    t = t.replace("ε", "epsilon")
    t = t.replace("λ", "lambda")
    t = t.replace("μ", "mu")
    t = t.replace("σ", "sigma")
    t = t.replace("φ", "phi")
    t = t.replace("ω", "omega")

    # Multiplication/division symbols
    t = t.replace("×", " times ").replace("*", " times ")
    t = t.replace("÷", " divided by ").replace("/", " divided by ")

    # Equals
    t = t.replace("=", " equals ")

    # Caret powers: a^2 -> a squared; a^3 -> a cubed; a^n -> a to the power of n
    def power_to_words(match: re.Match) -> str:
        base = match.group(1).strip()
        exp = match.group(2)
        if exp == "2":
            return f"{base} squared"
        if exp == "3":
            return f"{base} cubed"
        return f"{base} to the power of {exp}"

    t = re.sub(r"(\b[a-zA-Z]\w*)\s*\^\s*(\d+)", power_to_words, t)

    # sqrt(...) or √x -> square root of ...
    t = re.sub(r"sqrt\s*\(\s*([^\)]+)\)", r"square root of \1", t, flags=re.IGNORECASE)
    t = t.replace("√", "square root of ")

    # Parentheses: make them speakable but minimal
    t = t.replace("(", " ( ").replace(")", " ) ")

    # Collapse multiple spaces
    t = re.sub(r"\s+", " ", t).strip()
    return t

# ============================================================================
# PHASE 3: LLM WITH CONVERSATION MEMORY
# ============================================================================

def get_contextual_answer_with_memory(user_id: str, video_id: str, 
                                      session_id: str, question: str, 
                                      language: str = "en") -> tuple[str, int]:
    """
    OPTIMIZED: Generate contextual answer with caching and performance tracking.
    
    This function:
    1. Checks cache for similar questions
    2. Retrieves conversation history from session_manager
    3. Builds context-aware prompt with video metadata
    4. Calls OpenAI API with fallback handling
    5. Caches response for future use
    6. Updates session history and logs conversation
    
    Args:
        user_id: User identifier
        video_id: Current video identifier
        session_id: Active session identifier
        question: Student's question
        language: Language preference
        
    Returns:
        Tuple of (answer_text, tokens_used)
    """
    import time
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"[OPTIMIZED LLM] Processing with caching")
    print(f"{'='*60}")
    print(f"User: {user_id}")
    print(f"Video: {video_id}")
    print(f"Session: {session_id}")
    print(f"Question: '{question}'")
    print(f"Language: {language}")
    
    # ========================================================================
    # STEP 1: Check cache first
    # ========================================================================
    
    cached_response = get_cached_llm_response(question, video_id, language)
    if cached_response:
        response_time = time.time() - start_time
        performance_tracker.record_request(response_time, from_cache=True)
        
        print(f"🎯 Cache HIT! Response time: {response_time:.2f}s")
        print(f"Answer: {cached_response['answer'][:70]}...")
        
        # Still update session history for consistency
        session_manager.update_history(
            session_id=session_id,
            question=question,
            answer=cached_response['answer'],
            metadata=cached_response.get('metadata', {})
        )
        
        return cached_response['answer'], cached_response.get('tokens_used', 0)
    
    # ========================================================================
    # STEP 2: Get video metadata and conversation history
    # ========================================================================
    
    video_info = VIDEO_METADATA.get(video_id, {})
    video_title = video_info.get("title", "Unknown Topic")
    video_description = video_info.get("description", "")
    video_keywords = ', '.join(video_info.get('keywords', []))
    video_level = video_info.get("level", "general")
    
    conversation_history = session_manager.get_history(session_id)
    history_length = len(conversation_history)
    
    print(f"Video Context: {video_title} ({video_level})")
    print(f"Conversation History: {history_length} messages")
    
    # ========================================================================
    # STEP 3: Build optimized system prompt
    # ========================================================================
    
    system_prompt = _build_optimized_system_prompt(
        video_title, video_description, video_level, video_keywords, language
    )
    
    # ========================================================================
    # STEP 4: Build messages with error handling
    # ========================================================================
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if available
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current question
    messages.append({"role": "user", "content": question})
    
    print(f"Total messages to LLM: {len(messages)}")
    
    # ========================================================================
    # STEP 5: Call OpenAI API with retry logic
    # ========================================================================
    
    answer_text, tokens_used = _call_openai_with_retry(messages)
    
    # ========================================================================
    # STEP 6: Cache response and update session
    # ========================================================================
    
    response_data = {
        "answer": answer_text,
        "tokens_used": tokens_used,
        "metadata": {
            "tokens_used": tokens_used,
            "model": OPENAI_MODEL,
            "video_id": video_id,
            "user_id": user_id,
            "session_id": session_id
        }
    }
    
    # Cache the response
    cache_llm_response(question, video_id, response_data, language)
    
    # Update session history
    session_manager.update_history(
        session_id=session_id,
        question=question,
        answer=answer_text,
        metadata=response_data["metadata"]
    )
    
    # Log conversation
    try:
        conversation_logger.log_conversation(
            question=question,
            answer=answer_text,
            video_id=video_id,
            video_title=video_title,
            metadata=response_data["metadata"]
        )
    except Exception as e:
        print(f"⚠️  Warning: Could not log conversation: {e}")
    
    # Record performance
    response_time = time.time() - start_time
    performance_tracker.record_request(response_time, from_cache=False)
    
    print(f"✅ Response generated in {response_time:.2f}s")
    print(f"Answer: {answer_text[:70]}...")
    print(f"Tokens used: {tokens_used}")
    print(f"{'='*60}\n")
    
    # Clean markdown for TTS compatibility
    answer_text = clean_markdown_for_tts(answer_text)
    
    return answer_text, tokens_used


def _build_optimized_system_prompt(video_title: str, video_description: str, 
                                  video_level: str, video_keywords: str, 
                                  language: str = "en") -> str:
    """Build optimized system prompt with language support."""
    
    # Use the system prompts from language_config.py
    from language_config import SYSTEM_PROMPTS
    lang_instruction = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"])
    
    return f"""{lang_instruction}

**Current Video Topic:** {video_title}
**Video Description:** {video_description}
**Difficulty Level:** {video_level}
**Key Concepts:** {video_keywords}

**FORMATTING RULES:**
- Use clean, step-by-step formatting
- Use proper line breaks between steps
- Format each step clearly
- Use bullet points for lists
- Use bold for emphasis
- Show calculations clearly
- End with clear final answer
- Use normal symbols (π, ×, ÷, ^, √) or ASCII like r^2
- Make it visually appealing and easy to follow

**YOUR ROLE:**
- Answer questions about the video topic and RELATED concepts
- BE VERY LENIENT - if the question is about the SAME MATHEMATICAL OBJECT, ALWAYS ANSWER
- Think broadly: if it's the same shape, concept, or closely related idea → ANSWER!

**EXAMPLES OF LENIENT ANSWERING:**
- Video: "Area of a Circle"
  ✅ "What is area of circle?" - ANSWER (exact topic)
  ✅ "What is perimeter of circle?" - ANSWER (same shape - circle!)
  ✅ "What is circumference?" - ANSWER (same shape - circle!)
  ✅ "What is radius?" - ANSWER (circle property)
  ✅ "What is diameter?" - ANSWER (circle property)
  ✅ "How to calculate pi?" - ANSWER (used in circle formulas)
  ✅ "What are use cases?" - ANSWER (applications)
  ✅ "Real-life examples?" - ANSWER (applications)
  ✅ ANY question about circles or their properties - ANSWER

**WHEN TO DECLINE (VERY RARE):**
Only reject if the question is about a COMPLETELY DIFFERENT topic:
  ❌ Video is about circles, question is about logarithms - REJECT
  ❌ Video is about algebra, question is about trigonometry - REJECT
  ❌ Video is about geometry, question is about calculus derivatives - REJECT
  ❌ Video is about math, question is about chemistry - REJECT
  ❌ Personal questions, off-topic requests - REJECT

**GOLDEN RULE:** If it's the same shape, same type of math, or a student might reasonably ask it while watching this video → ANSWER!

**REJECTION MUST BE IN STUDENT'S LANGUAGE:**
- Rejection message: "I'm here to help you with {video_title}. That question is outside the scope of this video. Do you have any questions about [main topic]?"
- Translate this message to the student's language!
- Use simple, clear language appropriate for {video_level} level

**REAL-LIFE EXAMPLES:**
- For circles: Pizza slices, wheels, coins, clocks, sports fields
- For area: Painting walls, flooring, land measurement, fabric needed
- For circumference: Fencing a garden, running track length, tire size
- For radius/diameter: Distance from center, designing round tables
- Make examples culturally relevant and practical
- Help students see WHERE and WHY they'd use this in real life

**CONVERSATION MEMORY:**
- You can see the conversation history
- Reference previous questions if relevant
- Build on earlier explanations
- Answer follow-up questions naturally

Be helpful, encouraging, and supportive. Give students room to explore the topic deeply!"""


def _call_openai_with_retry(messages: list, max_retries: int = 3) -> tuple[str, int]:
    """Call OpenAI API with retry logic and error handling."""
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS
            )
            
            answer_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            
            return answer_text, tokens_used
            
        except Exception as e:
            print(f"❌ OpenAI API attempt {attempt + 1} failed: {e}")
            
            if attempt == max_retries - 1:
                # Final fallback
                print("🔄 Using fallback response...")
                return _get_fallback_response(messages), 0
            
            # Wait before retry
            import time
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return _get_fallback_response(messages), 0


def _get_fallback_response(messages: list) -> str:
    """Get fallback response when OpenAI API fails."""
    # Extract video context from system message
    system_msg = messages[0]["content"] if messages else ""
    video_title = "the current math topic"
    
    if "Current Video Topic:" in system_msg:
        try:
            video_title = system_msg.split("Current Video Topic:")[1].split("**")[0].strip()
        except:
            pass
    
    return f"""I'm here to help with {video_title}! However, I encountered a technical issue with the AI service. 

Please try asking your question again, and I'll do my best to provide a helpful explanation about the mathematical concepts you're studying.

If the problem persists, you might want to:
1. Check your internet connection
2. Try rephrasing your question
3. Contact support if the issue continues

I'm still here to help you learn! 📚"""


def get_performance_stats() -> dict:
    """Get performance statistics."""
    return performance_tracker.get_stats()


# ============================================================================
# PHASE 1: STREAMING VERSION - NEW FUNCTION (ADDITIVE)
# ============================================================================

def get_contextual_answer_with_memory_streaming(user_id: str, video_id: str, 
                                                session_id: str, question: str):
    """
    STREAMING VERSION: Generate contextual answer with real-time token streaming.
    
    This function is IDENTICAL to get_contextual_answer_with_memory() but:
    1. Uses stream=True in OpenAI API call
    2. Yields tokens as they arrive instead of returning full text
    3. Still updates session history and logs conversation
    
    Args:
        user_id: User identifier
        video_id: Current video identifier
        session_id: Active session identifier
        question: Student's question
    
    Yields:
        dict: Streaming chunks with format:
            {"type": "token", "content": "word"}
            {"type": "done", "full_text": "...", "tokens_used": 123}
            {"type": "error", "error": "..."}
    """
    
    print(f"\n{'='*60}")
    print(f"[STREAMING LLM] Real-time token generation")
    print(f"{'='*60}")
    print(f"User: {user_id}")
    print(f"Video: {video_id}")
    print(f"Session: {session_id}")
    print(f"Question: '{question}'")
    
    # Get video metadata for context (IDENTICAL to original)
    video_info = VIDEO_METADATA.get(video_id, {})
    video_title = video_info.get("title", "Unknown Topic")
    video_description = video_info.get("description", "")
    video_keywords = ', '.join(video_info.get('keywords', []))
    video_level = video_info.get("level", "general")
    
    print(f"Video Context: {video_title} ({video_level})")
    
    # ========================================================================
    # STEP 1: Retrieve conversation history from session (IDENTICAL)
    # ========================================================================
    
    conversation_history = session_manager.get_history(session_id)
    history_length = len(conversation_history)
    
    print(f"Conversation History: {history_length} messages ({history_length//2} turns)")
    
    # ========================================================================
    # STEP 2: Build System Prompt with video context (IDENTICAL)
    # ========================================================================
    
    system_prompt = f"""You are an expert, friendly, and encouraging AI Math Tutor helping a student who is watching a video.

**Current Video Topic:** {video_title}
**Video Description:** {video_description}
**Difficulty Level:** {video_level}
**Key Concepts:** {video_keywords}

TEXT OUTPUT RULES (UI):
- Use CLEAN, STEP-BY-STEP formatting like ChatGPT
- Start with the main formula: "Formula: [formula]"
- Use proper line breaks between sections (press Enter twice for spacing)
- Break down calculations step by step with clear separation
- Use clear section headers followed by line breaks
- Use normal symbols (π, ×, ÷, ^, √) or ASCII like r^2. Avoid LaTeX.
- Make it highly readable with proper line breaks and structure
- Include practical examples with clear explanations
- Format like: "Step 1: [content]\n\nStep 2: [content]" not "### Step 1"
- NEVER use ### or any markdown headers - use plain text with line breaks
- Always press Enter twice between major sections for clear separation
- CRITICAL: Each step must be on a new line with proper spacing
- Use format: "Step 1: [content]\n\nStep 2: [content]\n\nStep 3: [content]"
- Never write everything in one paragraph - always use line breaks

VOICE OUTPUT NOTE:
- A separate TTS layer speaks formulas in words. You can write symbols in text.
- Focus on clear symbolic formulas in the text answer; audio is handled separately.

**CRITICAL INSTRUCTION 2 - LANGUAGE:**
🌍 YOU MUST RESPOND IN THE SAME LANGUAGE AS THE STUDENT'S QUESTION
🌍 If student asks in Telugu, you answer in Telugu
🌍 If student asks in Hindi, you answer in Hindi
🌍 If student asks in Spanish, you answer in Spanish
🌍 This applies to BOTH answers AND rejections
🌍 Never switch to English unless the student uses English

**YOUR ROLE:**
- Answer questions about the video topic and RELATED concepts
- BE VERY LENIENT - if the question is about the SAME MATHEMATICAL OBJECT, ALWAYS ANSWER
- Think broadly: if it's the same shape, concept, or closely related idea → ANSWER!

**EXAMPLES OF LENIENT ANSWERING:**
- Video: "Area of a Circle"
  ✅ "What is area of circle?" - ANSWER (exact topic)
  ✅ "What is perimeter of circle?" - ANSWER (same shape - circle!)
  ✅ "What is circumference?" - ANSWER (same shape - circle!)
  ✅ "What is radius?" - ANSWER (circle property)
  ✅ "What is diameter?" - ANSWER (circle property)
  ✅ "How to calculate pi?" - ANSWER (used in circle formulas)
  ✅ "What are use cases?" - ANSWER (applications)
  ✅ "Real-life examples?" - ANSWER (applications)
  ✅ ANY question about circles or their properties - ANSWER
  
- Video: "Pythagorean Theorem"
  ✅ "What is Pythagorean theorem?" - ANSWER (exact topic)
  ✅ "What is a right triangle?" - ANSWER (same concept)
  ✅ "How to find hypotenuse?" - ANSWER (related to theorem)
  ✅ "What about other triangles?" - ANSWER (related shapes)
  ✅ "Where can I use it?" - ANSWER (applications)
  ✅ ANY question about triangles or the theorem - ANSWER

- Video: "Quadratic Equations"
  ✅ "What is quadratic equation?" - ANSWER (exact topic)
  ✅ "What is linear equation?" - ANSWER (related algebra)
  ✅ "How to solve equations?" - ANSWER (related skill)
  ✅ "What is factoring?" - ANSWER (solving method)
  ✅ ANY question about equations or polynomials - ANSWER

**WHEN TO DECLINE (VERY RARE):**
Only reject if the question is about a COMPLETELY DIFFERENT topic:
  ❌ Video is about circles, question is about logarithms - REJECT
  ❌ Video is about algebra, question is about trigonometry - REJECT
  ❌ Video is about geometry, question is about calculus derivatives - REJECT
  ❌ Video is about math, question is about chemistry - REJECT
  ❌ Personal questions, off-topic requests - REJECT

**GOLDEN RULE:** If it's the same shape, same type of math, or a student might reasonably ask it while watching this video → ANSWER!

**REJECTION MUST BE IN STUDENT'S LANGUAGE:**
🚫 If student asks in Telugu → Reject in Telugu
🚫 If student asks in Hindi → Reject in Hindi  
🚫 If student asks in Spanish → Reject in Spanish
🚫 NEVER reject in English unless student used English
- Rejection message structure: "I'm here to help you with {video_title}. That question is outside the scope of this video. Do you have any questions about [main topic]?"
- Translate this message to the student's language!
- Use simple, clear language appropriate for {video_level} level
- 🌍 CRITICAL: Match the student's language in ALL responses (answers AND rejections)
- 🌍 Look at the language of the question and respond in THAT EXACT LANGUAGE
- Keep answers concise (100-150 words for voice output)
- DO NOT use LaTeX, subscripts, superscripts, or Greek letters - use plain text
- Express formulas in words (e.g., "pi times radius squared")
- Speak naturally as if talking to a student, not writing text
- REMEMBER: No **, no *, no _, no # - plain text only!
- ALWAYS include a relevant REAL-LIFE EXAMPLE to help visualization:
  • For circles: Pizza slices, wheels, coins, clocks, sports fields
  • For area: Painting walls, flooring, land measurement, fabric needed
  • For circumference: Fencing a garden, running track length, tire size
  • For radius/diameter: Distance from center, designing round tables
  • Make examples culturally relevant and practical
  • Help students see WHERE and WHY they'd use this in real life

**CONVERSATION MEMORY:**
- You can see the conversation history
- Reference previous questions if relevant
- Build on earlier explanations
- Answer follow-up questions naturally

Be helpful, encouraging, and supportive. Give students room to explore the topic deeply!"""
    
    # ========================================================================
    # STEP 3: Build messages array with history injection (IDENTICAL)
    # ========================================================================
    
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Inject conversation history
    if conversation_history:
        print(f"Injecting {len(conversation_history)} historical messages...")
        messages.extend(conversation_history)
    
    # Add current question
    messages.append({
        "role": "user",
        "content": question
    })
    
    print(f"Total messages to LLM: {len(messages)}")
    print(f"🔄 Starting token stream...")
    
    # ========================================================================
    # STEP 4: Call OpenAI API with STREAMING enabled (ONLY DIFFERENCE)
    # ========================================================================
    
    full_response = ""
    tokens_used = 0
    
    try:
        stream = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
            stream=True  # 🔥 ONLY DIFFERENCE: stream=True
        )
        
        # Stream tokens as they arrive
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                token = chunk.choices[0].delta.content
                full_response += token
                
                # Yield token to frontend immediately
                yield {
                    "type": "token",
                    "content": token
                }
        
        # Estimate tokens used (OpenAI doesn't provide usage with streaming)
        # Rough estimate: ~4 chars = 1 token
        tokens_used = len(full_response) // 4 + len(question) // 4 + len(system_prompt) // 4
        
        print(f"\n✅ Stream complete: {len(full_response)} chars (~{tokens_used} tokens)")
        
    except Exception as e:
        print(f"❌ Streaming LLM Error: {e}")
        
        # Send error to frontend
        yield {
            "type": "error",
            "error": str(e)
        }
        
        # Fallback response
        full_response = f"I'm here to help with {video_title}! However, I encountered a technical issue. Please try asking your question again."
        tokens_used = 0
    
    # ========================================================================
    # STEP 5: Update session history with complete response (IDENTICAL)
    # ========================================================================
    
    session_manager.update_history(
        session_id=session_id,
        question=question,
        answer=full_response,
        metadata={
            "tokens_used": tokens_used,
            "model": OPENAI_MODEL,
            "video_id": video_id,
            "streaming": True
        }
    )
    
    print(f"Session updated with new turn (streaming)")
    
    # ========================================================================
    # STEP 6: Log conversation for revision system (IDENTICAL)
    # ========================================================================
    
    try:
        conversation_logger.log_conversation(
            question=question,
            answer=full_response,
            video_id=video_id,
            video_title=video_title,
            metadata={
                "tokens_used": tokens_used,
                "model": OPENAI_MODEL,
                "temperature": OPENAI_TEMPERATURE,
                "video_level": video_level,
                "video_keywords": video_info.get("keywords", []),
                "session_id": session_id,
                "user_id": user_id,
                "conversation_turn": history_length // 2 + 1,
                "streaming": True
            }
        )
    except Exception as e:
        print(f"⚠️  Warning: Could not log conversation: {e}")
    
    # ========================================================================
    # STEP 7: Send final completion signal
    # ========================================================================
    
    yield {
        "type": "done",
        "full_text": full_response,
        "tokens_used": tokens_used
    }
    
    print(f"{'='*60}\n")


def get_contextual_answer(video_id: str, question: str, use_mock: bool = False) -> str:
    """
    Generates a contextual answer using the LLM.
    
    Args:
        video_id: The ID of the currently playing video (e.g., 'Area_Circle').
        question: The student's transcribed question.
        use_mock: If True, uses mock responses (for testing without API costs).
        
    Returns:
        The text of the AI's answer.
    """
    # Get video metadata
    video_info = VIDEO_METADATA.get(video_id, {})
    video_title = video_info.get("title", "an unknown math concept")
    video_topic = video_info.get("topic", "Mathematics")
    video_difficulty = video_info.get("difficulty", "general")
    
    print("=" * 60)
    print("| LLM Service: Processing contextual query...")
    print(f"| Video ID: {video_id}")
    print(f"| Context: {video_title}")
    print(f"| Topic: {video_topic} | Level: {video_difficulty}")
    print(f"| Question: '{question}'")
    
    # Use mock responses if requested (saves API costs during testing)
    if use_mock:
        return _get_mock_response(video_id, question)
    
    # Construct the contextual prompt
    contextual_prompt = f"""


**System Prompt for AI Math Tutor:**

You are an expert, friendly, and highly focused math & science tutor. Your primary goal is to help a student understand the specific math concept presented in the video they are currently watching.

**Current Concept Focus:** **{question}** **Current Video ID:** {question}
**Difficulty Level:** {video_difficulty}

**CONSTRAINT 1 (Strict Focus):** You must **only** answer questions that are directly related to the **Current Concept Focus**. If the student deviates, politely decline and redirect them back to the current topic.

**CONSTRAINT 2 (Persona & Format):**
- Be a helpful, friendly, and encouraging tutor.
- Provide answers suitable for the **{video_difficulty}** level.
- Keep your answers concise, conversational, and direct.
- **Maximum Answer Length:** Do not exceed 700 tokens.

**CONSTRAINT 3 (TTS Output Format):**
- **DO NOT** use LaTeX, subscripts, superscripts, or Greek letters.
- Write variable names exactly as requested (e.g., use 'h1' and 'h2', not 'h\_1').
- Express all fractions and symbols using words (e.g., 'half multiplied by', 'equals', 'divided by').

**CORE KNOWLEDGE (To be supplied by your code):**
[Insert the specific, constrained knowledge/formula for the video concept here.] 
Example: "The core principle is decomposition. The area of a quadrilateral equals **half multiplied by the diagonal (d) multiplied by the sum of the two perpendicular heights (h1 plus h2)** of the triangles. Always use plain English for formulas."

---

**Student's Question (Transcribed):** "{question}"

**Your Task:** Provide a helpful, friendly voice response that adheres to all constraints.


"""
    
    try:
        # Call OpenAI API
        print("| Calling OpenAI API...")
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": contextual_prompt}
            ],
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        )
        
        # Extract answer
        answer_text = response.choices[0].message.content.strip()
        
        print(f"| LLM Answer: {answer_text[:70]}...")
        print(f"| Tokens used: {response.usage.total_tokens}")
        print("=" * 60)
        
        # Log conversation for revision and personalized learning
        try:
            conversation_logger.log_conversation(
                question=question,
                answer=answer_text,
                video_id=video_id,
                video_title=video_info.get("title", "Unknown"),
                metadata={
                    "tokens_used": response.usage.total_tokens,
                    "model": OPENAI_MODEL,
                    "temperature": OPENAI_TEMPERATURE,
                    "video_level": video_info.get("level", "unknown"),
                    "video_keywords": video_info.get("keywords", [])
                }
            )
        except Exception as e:
            print(f"| Warning: Could not log conversation: {e}")
        
        # Clean markdown for TTS compatibility
        answer_text = clean_markdown_for_tts(answer_text)
        
        return answer_text
        
    except Exception as e:
        print(f"| ERROR: OpenAI API call failed: {e}")
        print("| Falling back to mock response...")
        print("=" * 60)
        return _get_mock_response(video_id, question)


def _get_mock_response(video_id: str, question: str) -> str:
    """
    Fallback mock responses for testing without API costs.
    """
    MOCK_RESPONSES = {
        "Area_Circle": "That's a great question about the area of a circle! The pi (π) symbol is key because it represents the ratio of a circle's circumference to its diameter, meaning it perfectly scales the radius squared to get the area.",
        "PythagoreanTheorem": "You're asking about the sides of a right triangle. The theorem proves that the square of the hypotenuse (the longest side, 'c') is exactly equal to the sum of the squares of the other two sides ('a' and 'b').",
        "QuadraticFormula": "I see you're looking at the solution method! The square root part, b² - 4ac, is called the discriminant. It tells you whether the equation has two, one, or zero real solutions.",
        "default": "That's an interesting question! Based on your query, I can provide a general explanation. Let me know if you are referring to a specific math topic."
    }
    
    response = MOCK_RESPONSES.get(video_id, MOCK_RESPONSES["default"])
    print(f"| Mock Answer: {response[:70]}...")
    print("=" * 60)
    return response


def test_openai_connection() -> bool:
    """
    Test if OpenAI API key is valid and connection works.
    
    Returns:
        True if connection successful, False otherwise.
    """
    try:
        print("Testing OpenAI API connection...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'OK' if you can read this."}],
            max_tokens=10
        )
        print(f"✅ OpenAI API connected successfully!")
        print(f"   Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {e}")
        print(f"   Please check your API key in config.py")
        return False


if __name__ == "__main__":
    # Test the service
    print("=" * 60)
    print("Testing LLM Service")
    print("=" * 60)
    
    # Test with mock (no API cost)
    print("\n1. Testing with MOCK responses:")
    answer = get_contextual_answer("Area_Circle", "Why is pi used?", use_mock=True)
    print(f"\nFinal Answer: {answer}\n")
    
    # Test OpenAI connection (only if API key is set)
    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-your"):
        print("\n2. Testing REAL OpenAI API:")
        if test_openai_connection():
            answer = get_contextual_answer("Area_Circle", "Why is pi used?", use_mock=False)
            print(f"\nFinal Answer: {answer}\n")
    else:
        print("\n⚠️  OpenAI API key not configured. Update config.py to test real API.")
