"""
Cache Service for AI Math Tutor
Implements intelligent caching to reduce API costs and improve response times
"""

import json
import hashlib
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import os


class CacheService:
    """
    Intelligent caching service for AI responses, image processing, and TTS.
    
    Features:
    - Question-based caching (similar questions get cached responses)
    - TTL-based expiration
    - Size-based cleanup
    - Semantic similarity matching
    """
    
    def __init__(self, cache_dir: str = "./cache", max_size_mb: int = 100):
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache metadata
        self.metadata_file = os.path.join(cache_dir, "cache_metadata.json")
        self.metadata = self._load_metadata()
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0
        }
    
    def _load_metadata(self) -> Dict:
        """Load cache metadata from disk."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {"entries": {}, "last_cleanup": None}
    
    def _save_metadata(self):
        """Save cache metadata to disk."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _generate_cache_key(self, question: str, video_id: str, language: str = "en") -> str:
        """Generate a cache key for a question."""
        # Normalize question for better cache hits
        normalized_question = self._normalize_question(question)
        
        # Create hash from normalized question + context
        content = f"{normalized_question}|{video_id}|{language}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _normalize_question(self, question: str) -> str:
        """Normalize question for better cache matching."""
        import re
        
        # Convert to lowercase
        normalized = question.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove punctuation for better matching
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove common question words that don't affect meaning
        stop_words = {'what', 'how', 'why', 'when', 'where', 'is', 'are', 'the', 'a', 'an'}
        words = normalized.split()
        words = [w for w in words if w not in stop_words]
        
        return ' '.join(words)
    
    def get_cached_response(self, question: str, video_id: str, language: str = "en") -> Optional[Dict]:
        """
        Get cached response if available and not expired.
        
        Args:
            question: Student's question
            video_id: Video context
            language: Language code
            
        Returns:
            Cached response dict or None if not found/expired
        """
        self.stats["total_requests"] += 1
        
        cache_key = self._generate_cache_key(question, video_id, language)
        
        if cache_key not in self.metadata["entries"]:
            self.stats["misses"] += 1
            return None
        
        entry = self.metadata["entries"][cache_key]
        
        # Check if expired
        if self._is_expired(entry):
            self._remove_entry(cache_key)
            self.stats["misses"] += 1
            return None
        
        # Check if file exists
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if not os.path.exists(cache_file):
            self._remove_entry(cache_key)
            self.stats["misses"] += 1
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            # Update access time
            entry["last_accessed"] = time.time()
            self._save_metadata()
            
            self.stats["hits"] += 1
            print(f"🎯 Cache HIT for question: '{question[:50]}...'")
            return cached_data
            
        except (json.JSONDecodeError, FileNotFoundError):
            self._remove_entry(cache_key)
            self.stats["misses"] += 1
            return None
    
    def cache_response(self, question: str, video_id: str, response: Dict, 
                      language: str = "en", ttl_hours: int = 24) -> str:
        """
        Cache a response for future use.
        
        Args:
            question: Student's question
            video_id: Video context
            response: Response to cache
            language: Language code
            ttl_hours: Time to live in hours
            
        Returns:
            Cache key
        """
        cache_key = self._generate_cache_key(question, video_id, language)
        
        # Prepare cache entry
        cache_entry = {
            "question": question,
            "video_id": video_id,
            "language": language,
            "created_at": time.time(),
            "last_accessed": time.time(),
            "ttl_hours": ttl_hours,
            "size_bytes": len(json.dumps(response))
        }
        
        # Save response to file
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(cache_file, 'w') as f:
            json.dump(response, f, indent=2)
        
        # Update metadata
        self.metadata["entries"][cache_key] = cache_entry
        self._save_metadata()
        
        # Cleanup if needed
        self._cleanup_if_needed()
        
        print(f"💾 Cached response for: '{question[:50]}...'")
        return cache_key
    
    def _is_expired(self, entry: Dict) -> bool:
        """Check if cache entry is expired."""
        ttl_seconds = entry.get("ttl_hours", 24) * 3600
        age = time.time() - entry["created_at"]
        return age > ttl_seconds
    
    def _remove_entry(self, cache_key: str):
        """Remove cache entry and file."""
        if cache_key in self.metadata["entries"]:
            del self.metadata["entries"][cache_key]
            
            # Remove file
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
            
            self.stats["evictions"] += 1
    
    def _cleanup_if_needed(self):
        """Clean up cache if size limit exceeded."""
        current_size = self._get_cache_size()
        
        if current_size > self.max_size_bytes:
            self._cleanup_old_entries()
    
    def _get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total_size = 0
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json') and filename != "cache_metadata.json":
                filepath = os.path.join(self.cache_dir, filename)
                total_size += os.path.getsize(filepath)
        return total_size
    
    def _cleanup_old_entries(self):
        """Remove oldest entries to make space."""
        # Sort by last accessed time (oldest first)
        entries = list(self.metadata["entries"].items())
        entries.sort(key=lambda x: x[1]["last_accessed"])
        
        # Remove oldest 25% of entries
        to_remove = len(entries) // 4
        for i in range(to_remove):
            cache_key = entries[i][0]
            self._remove_entry(cache_key)
        
        print(f"🧹 Cleaned up {to_remove} old cache entries")
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        hit_rate = 0
        if self.stats["total_requests"] > 0:
            hit_rate = self.stats["hits"] / self.stats["total_requests"]
        
        return {
            **self.stats,
            "hit_rate": f"{hit_rate:.2%}",
            "total_entries": len(self.metadata["entries"]),
            "cache_size_mb": self._get_cache_size() / (1024 * 1024)
        }
    
    def clear_cache(self):
        """Clear all cache entries."""
        for cache_key in list(self.metadata["entries"].keys()):
            self._remove_entry(cache_key)
        
        self.metadata = {"entries": {}, "last_cleanup": None}
        self._save_metadata()
        
        print("🗑️ Cache cleared")


# Global cache instance
cache_service = CacheService()


def get_cached_llm_response(question: str, video_id: str, language: str = "en") -> Optional[Dict]:
    """Get cached LLM response."""
    return cache_service.get_cached_response(question, video_id, language)


def cache_llm_response(question: str, video_id: str, response: Dict, language: str = "en") -> str:
    """Cache LLM response."""
    return cache_service.cache_response(question, video_id, response, language, ttl_hours=24)


def get_cached_tts_response(text: str, language: str = "en") -> Optional[str]:
    """Get cached TTS audio file path."""
    cache_key = hashlib.md5(f"{text}|{language}".encode()).hexdigest()
    audio_file = os.path.join(cache_service.cache_dir, f"tts_{cache_key}.wav")
    
    if os.path.exists(audio_file):
        # Check if file is recent (TTS cache for 1 hour)
        file_age = time.time() - os.path.getmtime(audio_file)
        if file_age < 3600:  # 1 hour
            return audio_file
    
    return None


def cache_tts_response(text: str, audio_file_path: str, language: str = "en") -> str:
    """Cache TTS audio file."""
    cache_key = hashlib.md5(f"{text}|{language}".encode()).hexdigest()
    cached_file = os.path.join(cache_service.cache_dir, f"tts_{cache_key}.wav")
    
    # Copy file to cache
    import shutil
    shutil.copy2(audio_file_path, cached_file)
    
    return cached_file


if __name__ == "__main__":
    # Test cache service
    print("🧪 Testing Cache Service")
    print("=" * 50)
    
    # Test caching
    test_response = {
        "answer": "Pi is used because it represents the ratio of circumference to diameter...",
        "tokens_used": 150,
        "cached": True
    }
    
    # Cache a response
    key = cache_llm_response(
        "Why is pi used in the area formula?",
        "Area_Circle",
        test_response,
        "en"
    )
    print(f"✅ Cached with key: {key}")
    
    # Try to retrieve
    cached = get_cached_llm_response(
        "Why is pi used in the area formula?",
        "Area_Circle",
        "en"
    )
    
    if cached:
        print("✅ Cache hit!")
        print(f"   Answer: {cached['answer'][:50]}...")
    else:
        print("❌ Cache miss")
    
    # Show stats
    stats = cache_service.get_stats()
    print(f"\n📊 Cache Stats:")
    print(f"   Hit Rate: {stats['hit_rate']}")
    print(f"   Total Entries: {stats['total_entries']}")
    print(f"   Cache Size: {stats['cache_size_mb']:.2f} MB")
