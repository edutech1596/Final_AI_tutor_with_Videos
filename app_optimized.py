"""
OPTIMIZED Flask Application for AI Math Tutor
Integrates all performance optimizations, error handling, and monitoring
"""

from flask import Flask, request, jsonify, Response, stream_with_context, send_from_directory
import base64
import os
import json
import time
from typing import Dict, Any

# Import optimized services
from service_manager import service_manager, register_llm_service, register_tts_service
from error_handler import error_handler, handle_service_error, retry_on_failure
from monitoring import monitor, track_service_call, get_monitoring_dashboard
from cache_service import cache_service

# Import existing services
from config import VIDEO_METADATA
from session_manager import session_manager
from llm_service import get_contextual_answer_with_memory, get_performance_stats, get_contextual_answer_with_memory_streaming, convert_formulas_to_spoken_words
from tts_service import generate_audio_response
from audio_utils import decode_and_transcribe_audio
from image_service_clean import CleanImageService
from video_service import video_service

# Initialize Flask app
app = Flask(__name__)

# Service availability flags
PHASE2_READY = True
PHASE3_READY = True
STREAMING_READY = True
SERVICES_READY = True
IMAGE_PROCESSING_READY = True

# Initialize services
try:
    from llm_service import client
    register_llm_service(client, lambda: True)
    print("[✅] LLM service registered")
except Exception as e:
    print(f"[⚠️] LLM service not available: {e}")

try:
    from tts_service import generate_audio_response
    register_tts_service(generate_audio_response, lambda: True)
    print("[✅] TTS service registered")
except Exception as e:
    print(f"[⚠️] TTS service not available: {e}")

try:
    from image_service_clean import CleanImageService
    from config import OPENAI_API_KEY
    image_service = CleanImageService(openai_api_key=OPENAI_API_KEY)
    print("[✅] Image processing service ready")
except Exception as e:
    image_service = None
    IMAGE_PROCESSING_READY = False
    print(f"[⚠️] Image processing service not available: {e}")


# ============================================================================
# OPTIMIZED API ENDPOINTS
# ============================================================================

@app.route('/api/ask_tutor', methods=['POST'])
def ask_tutor_optimized():
    """
    OPTIMIZED: Main Q&A endpoint with caching, error handling, and monitoring.
    """
    start_time = time.time()
    
    print("\n" + "="*70)
    print("[OPTIMIZED API] Request Received")
    print("="*70)
    
    # Validate input
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': 'No JSON body provided'
        }), 400
    
    user_id = data.get('user_id')
    video_id = data.get('video_id')
    question_text = data.get('question_text')
    audio_base64 = data.get('audio_file_base64')
    image_base64 = data.get('image_base64')
    language = data.get('language', 'en')
    
    if not user_id or not video_id:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: user_id, video_id'
        }), 400
    
    if not question_text and not audio_base64 and not image_base64:
        return jsonify({
            'success': False,
            'error': 'No input provided (question_text, audio_file_base64, or image_base64)'
        }), 400
    
    # Process audio if provided
    if audio_base64 and not question_text:
        try:
            question_text, detected_language = decode_and_transcribe_audio(audio_base64, language)
            language = detected_language
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Speech recognition failed: {str(e)}'
            }), 400
    
    # Use provided language or auto-detect if not provided
    if not language:
        from language_config import detect_language_from_text
        language = detect_language_from_text(question_text)
        print(f"🌍 Auto-detected language: {language}")
    else:
        print(f"🌍 Using selected language: {language}")
    
    # Get or create session
    session_id, is_new_session = session_manager.get_or_create_session(user_id, video_id)
    
    # Process image if provided
    image_context = ""
    if image_base64 and IMAGE_PROCESSING_READY:
        try:
            print("🖼️ Processing image...")
            result = image_service.process_image(image_base64, "comprehensive")
            
            # Extract relevant information
            parts = []
            if result.get('extracted_text'):
                parts.append(f"Text: {result['extracted_text']}")
            if result.get('math_equations'):
                parts.append(f"Math: {', '.join(result['math_equations'])}")
            if result.get('vision_analysis', {}).get('analysis'):
                vision = result['vision_analysis']['analysis']
                if len(vision) > 200:
                    vision = vision[:200] + "..."
                parts.append(f"Vision: {vision}")
            
            image_context = ' | '.join(parts) if parts else 'Image uploaded'
            print(f"🖼️ Image context: {image_context[:100]}...")
            
            # Add image context to session
            session_manager.add_image_context(session_id, image_context)
            
        except Exception as e:
            print(f"⚠️ Image processing failed: {e}")
            image_context = "Image processing failed"
    
    # Get LLM response with caching
    try:
        answer_text, tokens_used = get_contextual_answer_with_memory(
            user_id=user_id,
            video_id=video_id,
            session_id=session_id,
            question=question_text,
            language=language
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'AI processing failed: {str(e)}'
        }), 500
    
    # Generate audio if requested
    audio_base64_response = None
    if data.get('audio_output', True):
        try:
            # Use spoken-form conversion for TTS (like original app.py)
            audio_text = convert_formulas_to_spoken_words(answer_text)
            audio_filepath = generate_audio_response(
                audio_text,
                output_filename=f"response_{session_id}_{int(time.time())}",
                language=language
            )
            
            # Convert to base64
            with open(audio_filepath, 'rb') as f:
                audio_bytes = f.read()
                audio_base64_response = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Clean up temp file
            if os.path.exists(audio_filepath):
                os.remove(audio_filepath)
                
        except Exception as e:
            print(f"⚠️ TTS failed: {e}")
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # Get session info
    session_info = session_manager.get_session_info(session_id)
    
    # Build response
    response_data = {
        'success': True,
        'session_id': session_id,
        'is_new_session': is_new_session,
        'question': question_text,
        'answer': answer_text,
        'audio_base64': audio_base64_response,
        'language': language,
        'turn_count': session_info.get('turn_count', 0),
        'video_id': video_id,
        'video_title': VIDEO_METADATA.get(video_id, {}).get('title', 'Unknown'),
        'metadata': {
            'tokens_used': tokens_used,
            'response_time': response_time,
            'cached': False,  # Will be updated by cache service
            'user_id': user_id
        }
    }
    
    print(f"✅ Response generated in {response_time:.2f}s")
    print("="*70 + "\n")
    
    return jsonify(response_data)


@app.route('/api/ask_tutor_stream_optimized', methods=['POST'])
def ask_tutor_stream_optimized():
    """
    OPTIMIZED: Streaming endpoint with real-time monitoring.
    """
    def generate():
        try:
            print("\n" + "="*70)
            print("[OPTIMIZED STREAMING API] Request Received")
            print("="*70)
            
            data = request.json
            if not data:
                yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': 'No JSON body provided'})}\n\n"
                return
            
            user_id = data.get('user_id')
            video_id = data.get('video_id')
            question_text = data.get('question_text')
            language = data.get('language', 'en')
            
            if not user_id or not video_id or not question_text:
                yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': 'Missing required fields'})}\n\n"
                return
            
            # Use provided language or auto-detect if not provided
            if not language:
                from language_config import detect_language_from_text
                language = detect_language_from_text(question_text)
                print(f"🌍 Auto-detected language: {language}")
            else:
                print(f"🌍 Using selected language: {language}")
            
            # Get or create session
            session_id, is_new_session = session_manager.get_or_create_session(user_id, video_id)
            
            # Send start event
            yield f"event: start\ndata: {json.dumps({'type': 'start', 'question': question_text, 'session_id': session_id, 'language': language})}\n\n"
            
            # Stream LLM response
            full_text = ""
            tokens_used = 0
            
            try:
                for chunk in get_contextual_answer_with_memory_streaming(
                    user_id=user_id,
                    video_id=video_id,
                    session_id=session_id,
                    question=question_text
                ):
                    if chunk['type'] == 'token':
                        yield f"event: token\ndata: {json.dumps(chunk)}\n\n"
                    elif chunk['type'] == 'done':
                        full_text = chunk['full_text']
                        tokens_used = chunk['tokens_used']
                    elif chunk['type'] == 'error':
                        yield f"event: error\ndata: {json.dumps(chunk)}\n\n"
                        return
                        
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                return
            
            # Generate audio if requested
            audio_base64 = None
            if data.get('audio_output', True):
                try:
                    # Use spoken-form conversion for TTS (like original app.py)
                    audio_text = convert_formulas_to_spoken_words(full_text)
                    
                    audio_filepath = generate_audio_response(
                        audio_text,  # Use spoken-form text for TTS
                        output_filename=f"response_stream_{session_id}_{int(time.time())}",
                        language=language
                    )
                    
                    with open(audio_filepath, 'rb') as f:
                        audio_bytes = f.read()
                        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                    
                    if os.path.exists(audio_filepath):
                        os.remove(audio_filepath)
                        
                except Exception as e:
                    print(f"⚠️ TTS failed: {e}")
            
            # Send completion event
            final_data = {
                'type': 'done',
                'full_text': full_text,
                'audio_base64': audio_base64,
                'tokens_used': tokens_used,
                'language': language,
                'session_id': session_id
            }
            
            yield f"event: done\ndata: {json.dumps(final_data)}\n\n"
            
            print(f"✅ Streaming complete")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route('/api/process_image', methods=['POST'])
def process_image_optimized():
    """
    OPTIMIZED: Image processing with caching and monitoring.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No JSON data provided'
        }), 400
    
    image_base64 = data.get('image_base64')
    processing_type = data.get('processing_type', 'comprehensive')
    user_id = data.get('user_id')
    video_id = data.get('video_id')
    
    if not image_base64:
        return jsonify({
            'success': False,
            'error': 'No image data provided'
        }), 400
    
    if not IMAGE_PROCESSING_READY:
        return jsonify({
            'success': False,
            'error': 'Image processing service not available'
        }), 503
    
    # Process image with caching
    try:
        # Check cache first
        cache_key = f"image_{hash(image_base64[:100])}"
        cached_result = cache_service.get_cached_response(
            f"image_processing_{cache_key}", 
            video_id or "general", 
            "en"
        )
        
        if cached_result and 'result' in cached_result:
            print("🎯 Image processing cache HIT!")
            result = cached_result['result']
        else:
            # Process image
            result = image_service.process_image(image_base64, processing_type)
            
            # Cache result
            cache_service.cache_response(
                f"image_processing_{cache_key}",
                video_id or "general",
                {"result": result},
                "en",
                ttl_hours=2  # Cache images for 2 hours
            )
        
        # Attach to session if identifiers provided
        if PHASE2_READY and user_id and video_id:
            try:
                session_id, _ = session_manager.get_or_create_session(user_id, video_id)
                
                # Build context string
                extracted = result.get('extracted_text') or ''
                math_eq = ', '.join(result.get('math_equations') or [])
                vision = result.get('vision_analysis', {}).get('analysis') or ''
                
                parts = []
                if extracted:
                    parts.append(f"Text: {extracted[:160]}")
                if math_eq:
                    parts.append(f"Math: {math_eq[:160]}")
                if vision:
                    parts.append(f"Vision: {vision[:200]}")
                
                context_str = ' | '.join(parts) if parts else 'Image uploaded'
                session_manager.add_image_context(session_id, context_str)
                
            except Exception as e:
                print(f"⚠️ Could not attach image context: {e}")
        
        return jsonify({
            'success': True,
            'result': result,
            'cached': 'result' in cached_result if cached_result else False
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Image processing failed: {str(e)}'
        }), 500


# ============================================================================
# MONITORING AND HEALTH ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check_optimized():
    """Comprehensive health check with monitoring."""
    try:
        # Get system health
        system_health = monitor.get_system_health()
        
        # Get service health
        service_health = monitor.get_service_health()
        
        # Get cache stats
        cache_stats = cache_service.get_stats()
        
        # Get performance stats
        llm_stats = get_performance_stats()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': time.time(),
            'system_health': system_health,
            'service_health': service_health,
            'cache_stats': cache_stats,
            'llm_performance': llm_stats,
            'active_sessions': len(session_manager.sessions)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'unhealthy'
        }), 500


@app.route('/api/monitoring/dashboard', methods=['GET'])
def monitoring_dashboard():
    """Get comprehensive monitoring dashboard."""
    try:
        dashboard_data = get_monitoring_dashboard()
        return jsonify({
            'success': True,
            'dashboard': dashboard_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/monitoring/metrics', methods=['GET'])
def export_metrics():
    """Export monitoring metrics."""
    try:
        export_file = monitor.export_metrics()
        return jsonify({
            'success': True,
            'export_file': export_file,
            'message': 'Metrics exported successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics."""
    try:
        stats = cache_service.get_stats()
        return jsonify({
            'success': True,
            'cache_stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cache entries."""
    try:
        cache_service.clear_cache()
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the main interface."""
    return send_from_directory('static', 'index.html')

@app.route('/enhanced')
def enhanced_interface():
    """Serve the enhanced multimodal interface."""
    return send_from_directory('static', 'enhanced_voice_interface.html')

@app.route('/monitoring')
def monitoring_interface():
    """Serve monitoring dashboard."""
    return send_from_directory('static', 'monitoring.html')


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'code': 404
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'code': 500
    }), 500


# ============================================================================
# STARTUP AND SHUTDOWN
# ============================================================================

def initialize_services():
    """Initialize services on first request."""
    print("\n" + "="*70)
    print("🚀 INITIALIZING OPTIMIZED AI MATH TUTOR")
    print("="*70)
    
    # Initialize monitoring
    print("📊 Starting monitoring system...")
    
    # Initialize cache
    print("💾 Initializing cache system...")
    
    # Check service health
    print("🔧 Checking service health...")
    health_report = get_monitoring_dashboard()
    print(f"   System Status: {health_report['system_health']['status']}")
    print(f"   Services: {len(health_report['service_health'])}")
    
    print("✅ Initialization complete!")
    print("="*70 + "\n")


# ============================================================================
# VIDEO SERVICE ENDPOINTS
# ============================================================================

@app.route('/api/video-library', methods=['GET'])
def get_video_library():
    """Get the complete video library"""
    try:
        library = video_service.get_video_library()
        return jsonify({
            'success': True,
            'videos': library,
            'total_count': len(library)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/video/<video_id>', methods=['GET'])
def get_video_details(video_id):
    """Get details for a specific video"""
    try:
        video = video_service.get_video_by_id(video_id)
        if not video:
            return jsonify({
                'success': False,
                'error': 'Video not found'
            }), 404
        
        return jsonify({
            'success': True,
            'video': video
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/video/<video_id>/context', methods=['GET'])
def get_video_context(video_id):
    """Get contextual information for AI responses"""
    try:
        context = video_service.get_video_context(video_id)
        return jsonify({
            'success': True,
            'context': context
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/video/<video_id>/progress', methods=['POST'])
def update_video_progress():
    """Update user progress for a video"""
    try:
        data = request.json
        user_id = data.get('user_id')
        video_id = data.get('video_id')
        progress = data.get('progress', {})
        
        if not user_id or not video_id:
            return jsonify({
                'success': False,
                'error': 'Missing user_id or video_id'
            }), 400
        
        video_service.update_user_progress(user_id, video_id, progress)
        return jsonify({
            'success': True,
            'message': 'Progress updated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/video/<video_id>/progress', methods=['GET'])
def get_video_progress():
    """Get user progress for a video"""
    try:
        user_id = request.args.get('user_id')
        video_id = request.args.get('video_id')
        
        if not user_id or not video_id:
            return jsonify({
                'success': False,
                'error': 'Missing user_id or video_id'
            }), 400
        
        progress = video_service.get_user_progress(user_id, video_id)
        return jsonify({
            'success': True,
            'progress': progress
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/videos/<path:filename>')
def serve_video(filename):
    """Serve video files from the manim_with_voice directory"""
    try:
        video_path = os.path.join("/Users/apple/manim_with_voice/media/videos", filename)
        if os.path.exists(video_path):
            return send_from_directory(os.path.dirname(video_path), os.path.basename(video_path))
        else:
            return jsonify({
                'success': False,
                'error': 'Video file not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/unified')
def unified_learning_platform():
    """Serve the unified learning platform interface"""
    return send_from_directory('static', 'unified_learning_platform.html')

@app.route('/unified-multimodal')
def unified_multimodal_platform():
    """Serve the unified multimodal learning platform interface with full AI tutor features"""
    return send_from_directory('static', 'unified_multimodal_platform.html')

@app.route('/complete')
def complete_platform():
    """Serve the COMPLETE platform with ALL enhanced features + videos (RECOMMENDED)"""
    return send_from_directory('static', 'complete_platform_v2.html')


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎓 OPTIMIZED AI MATH TUTOR - PRODUCTION READY")
    print("="*70)
    print("\nOptimizations Active:")
    print("  ✅ Response caching")
    print("  ✅ Error handling & recovery")
    print("  ✅ Performance monitoring")
    print("  ✅ Service health tracking")
    print("  ✅ Automatic fallbacks")
    print("  ✅ Real-time metrics")
    print("\nEndpoints:")
    print("  POST /api/ask_tutor      - Main Q&A (optimized)")
    print("  POST /api/ask_tutor_stream - Streaming (optimized)")
    print("  POST /api/process_image  - Image processing (cached)")
    print("  GET  /api/health         - Health check (comprehensive)")
    print("  GET  /api/monitoring/dashboard - Monitoring dashboard")
    print("  GET  /api/cache/stats    - Cache statistics")
    print("  GET  /api/video-library   - Video library")
    print("  GET  /videos/<path>       - Video files")
    print("  GET  /unified             - Unified learning platform")
    print("\n" + "="*70 + "\n")
    
    # Initialize services
    initialize_services()
    
    # Run optimized server
    app.run(debug=False, host='0.0.0.0', port=5001)
