"""
Session Manager: Stateful Conversation Memory for AI Math Tutor

Manages multi-turn conversations with session-based memory that:
- Retains history within the same video_id
- Automatically clears when video_id changes
- Tracks conversations by user_id and video_id
"""

import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class SessionManager:
    """
    Manages conversation sessions with memory retention and automatic clearing.
    
    Session Rules:
    1. Memory is kept active for the same (user_id, video_id) pair
    2. Memory is cleared when video_id changes
    3. Memory is cleared on explicit end_session() call
    """
    
    def __init__(self):
        """Initialize the session manager with in-memory storage."""
        # Active sessions: {session_id: session_data}
        self.sessions: Dict[str, Dict] = {}
        
        # User to session mapping: {user_id: session_id}
        self.user_to_session: Dict[str, str] = {}
        
        # Session metadata for tracking
        self.session_metadata: Dict[str, Dict] = {}
    
    
    def _generate_session_id(self, user_id: str, video_id: str) -> str:
        """
        Generate a unique session ID.
        
        Args:
            user_id: The user identifier.
            video_id: The video identifier.
            
        Returns:
            A unique session ID.
        """
        timestamp = int(time.time() * 1000)
        return f"session_{user_id}_{video_id}_{timestamp}"
    
    
    def get_or_create_session(self, user_id: str, video_id: str) -> Tuple[str, bool]:
        """
        Get existing session or create new one if video_id changed.
        
        Args:
            user_id: The user identifier.
            video_id: The current video identifier.
            
        Returns:
            Tuple of (session_id, is_new_session)
        """
        # Check if user has an active session
        if user_id in self.user_to_session:
            old_session_id = self.user_to_session[user_id]
            old_session = self.sessions.get(old_session_id)
            
            if old_session and old_session['video_id'] == video_id:
                # Same video - continue existing session
                print(f"[SessionManager] Continuing session {old_session_id}")
                return old_session_id, False
            else:
                # Video changed - clear old session and create new one
                print(f"[SessionManager] Video changed: {old_session.get('video_id')} -> {video_id}")
                print(f"[SessionManager] Clearing old session {old_session_id}")
                self._clear_session(old_session_id)
        
        # Create new session
        session_id = self._generate_session_id(user_id, video_id)
        
        self.sessions[session_id] = {
            'user_id': user_id,
            'video_id': video_id,
            'history': [],  # List of {role, content} dicts
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'turn_count': 0,
            # Recent image contexts associated with this session (strings)
            'image_contexts': []
        }
        
        self.user_to_session[user_id] = session_id
        
        self.session_metadata[session_id] = {
            'total_questions': 0,
            'total_tokens': 0,
            'video_title': None  # Will be populated from VIDEO_METADATA
        }
        
        print(f"[SessionManager] Created new session {session_id} for video {video_id}")
        return session_id, True
    
    
    def get_history(self, session_id: str) -> List[Dict]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: The session identifier.
            
        Returns:
            List of conversation turns in OpenAI message format.
        """
        session = self.sessions.get(session_id)
        if not session:
            print(f"[SessionManager] Warning: Session {session_id} not found")
            return []
        
        return session['history']
    
    
    def update_history(self, session_id: str, question: str, answer: str, 
                       metadata: Optional[Dict] = None):
        """
        Add a new Q&A turn to the session history.
        
        Args:
            session_id: The session identifier.
            question: The user's question.
            answer: The AI's answer.
            metadata: Optional metadata (tokens, etc.).
        """
        session = self.sessions.get(session_id)
        if not session:
            print(f"[SessionManager] Error: Cannot update non-existent session {session_id}")
            return
        
        # Add user message
        session['history'].append({
            'role': 'user',
            'content': question
        })
        
        # Add assistant message
        session['history'].append({
            'role': 'assistant',
            'content': answer
        })
        
        # Update session metadata
        session['last_activity'] = datetime.now().isoformat()
        session['turn_count'] += 1
        
        # Update session statistics
        if session_id in self.session_metadata:
            self.session_metadata[session_id]['total_questions'] += 1
            if metadata and 'tokens_used' in metadata:
                self.session_metadata[session_id]['total_tokens'] += metadata['tokens_used']
        
        print(f"[SessionManager] Updated session {session_id} (Turn {session['turn_count']})")
    
    
    def _clear_session(self, session_id: str):
        """
        Clear a specific session (internal method).
        
        Args:
            session_id: The session identifier.
        """
        if session_id in self.sessions:
            user_id = self.sessions[session_id]['user_id']
            
            # Remove from user mapping
            if user_id in self.user_to_session and self.user_to_session[user_id] == session_id:
                del self.user_to_session[user_id]
            
            # Remove session data
            del self.sessions[session_id]
            
            # Keep metadata for analytics (optional)
            # del self.session_metadata[session_id]
            
            print(f"[SessionManager] Cleared session {session_id}")
    
    
    def end_session(self, user_id: str) -> bool:
        """
        Explicitly end a user's current session.
        
        Args:
            user_id: The user identifier.
            
        Returns:
            True if session was ended, False if no active session.
        """
        if user_id in self.user_to_session:
            session_id = self.user_to_session[user_id]
            self._clear_session(session_id)
            print(f"[SessionManager] Ended session for user {user_id}")
            return True
        
        print(f"[SessionManager] No active session for user {user_id}")
        return False
    
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get detailed information about a session.
        
        Args:
            session_id: The session identifier.
            
        Returns:
            Session information or None if not found.
        """
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        metadata = self.session_metadata.get(session_id, {})
        
        return {
            'session_id': session_id,
            'user_id': session['user_id'],
            'video_id': session['video_id'],
            'video_title': metadata.get('video_title'),
            'created_at': session['created_at'],
            'last_activity': session['last_activity'],
            'turn_count': session['turn_count'],
            'total_questions': metadata.get('total_questions', 0),
            'total_tokens': metadata.get('total_tokens', 0),
            'history_length': len(session['history']),
            'image_context_count': len(session.get('image_contexts', []))
        }
    
    
    def get_all_sessions(self) -> List[Dict]:
        """
        Get information about all active sessions.
        
        Returns:
            List of session information dictionaries.
        """
        return [self.get_session_info(sid) for sid in self.sessions.keys()]
    
    
    def cleanup_inactive_sessions(self, max_age_seconds: int = 3600):
        """
        Clean up sessions that have been inactive for too long.
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 1 hour).
        """
        current_time = time.time()
        sessions_to_clear = []
        
        for session_id, session in self.sessions.items():
            last_activity = datetime.fromisoformat(session['last_activity'])
            age = current_time - last_activity.timestamp()
            
            if age > max_age_seconds:
                sessions_to_clear.append(session_id)
        
        for session_id in sessions_to_clear:
            print(f"[SessionManager] Cleaning up inactive session {session_id}")
            self._clear_session(session_id)
        
        return len(sessions_to_clear)

    # ------------------------- IMAGE CONTEXT MEMORY -------------------------
    def add_image_context(self, session_id: str, context: str, max_keep: int = 5):
        """Attach a concise image context string to a session's memory."""
        session = self.sessions.get(session_id)
        if not session:
            print(f"[SessionManager] Warning: cannot add image context, session {session_id} not found")
            return
        if not context:
            return
        session.setdefault('image_contexts', []).append(context.strip())
        # Keep only last N
        if len(session['image_contexts']) > max_keep:
            session['image_contexts'] = session['image_contexts'][-max_keep:]
        session['last_activity'] = datetime.now().isoformat()

    def get_recent_image_contexts(self, session_id: str, last_k: int = 3) -> list:
        """Return up to last_k recent image contexts for this session."""
        session = self.sessions.get(session_id)
        if not session:
            return []
        contexts = session.get('image_contexts', [])
        if last_k <= 0:
            return []
        return contexts[-last_k:]


# Global session manager instance
session_manager = SessionManager()


# Test script
if __name__ == "__main__":
    print("=" * 70)
    print("SESSION MANAGER TEST")
    print("=" * 70)
    print()
    
    # Test 1: Create new session
    print("[Test 1] Creating session for user1 watching Area_Circle...")
    session_id1, is_new = session_manager.get_or_create_session("user1", "Area_Circle")
    print(f"Result: session_id={session_id1}, is_new={is_new}")
    print()
    
    # Test 2: Add conversation to session
    print("[Test 2] Adding Q&A to session...")
    session_manager.update_history(
        session_id1,
        "Why is pi used in the area formula?",
        "Pi represents the ratio of a circle's circumference to its diameter...",
        metadata={"tokens_used": 150}
    )
    history = session_manager.get_history(session_id1)
    print(f"History length: {len(history)} messages")
    print()
    
    # Test 3: Continue same session (same video)
    print("[Test 3] User asks follow-up question (same video)...")
    session_id2, is_new = session_manager.get_or_create_session("user1", "Area_Circle")
    print(f"Result: session_id={session_id2}, is_new={is_new}")
    print(f"Same session? {session_id1 == session_id2}")
    print()
    
    # Test 4: Video change triggers new session
    print("[Test 4] User switches to PythagoreanTheorem...")
    session_id3, is_new = session_manager.get_or_create_session("user1", "PythagoreanTheorem")
    print(f"Result: session_id={session_id3}, is_new={is_new}")
    print(f"Different session? {session_id1 != session_id3}")
    history = session_manager.get_history(session_id3)
    print(f"New session history: {len(history)} messages (should be 0)")
    print()
    
    # Test 5: Session info
    print("[Test 5] Getting session info...")
    info = session_manager.get_session_info(session_id3)
    print(f"Session info: {info}")
    print()
    
    # Test 6: End session
    print("[Test 6] Ending session for user1...")
    ended = session_manager.end_session("user1")
    print(f"Session ended: {ended}")
    all_sessions = session_manager.get_all_sessions()
    print(f"Active sessions remaining: {len(all_sessions)}")
    print()
    
    print("=" * 70)
    print("✅ SESSION MANAGER TEST COMPLETE")
    print("=" * 70)

