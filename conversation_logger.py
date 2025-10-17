"""
Conversation Logger - Save Q&A for Revision and Personalized Learning
Stores all student questions and AI answers for future review
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class ConversationLogger:
    """
    Manages conversation history for revision and personalized learning.
    """
    
    def __init__(self, log_directory: str = "./conversation_history"):
        """
        Initialize the conversation logger.
        
        Args:
            log_directory: Directory to store conversation logs.
        """
        self.log_directory = log_directory
        os.makedirs(log_directory, exist_ok=True)
        
        # Main log file (all conversations)
        self.main_log_file = os.path.join(log_directory, "all_conversations.json")
        
        # Daily log file
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_log_file = os.path.join(log_directory, f"conversations_{today}.json")
        
        # Initialize files if they don't exist
        if not os.path.exists(self.main_log_file):
            self._save_json(self.main_log_file, [])
        if not os.path.exists(self.daily_log_file):
            self._save_json(self.daily_log_file, [])
    
    
    def log_conversation(self, 
                        question: str, 
                        answer: str, 
                        video_id: str = None,
                        video_title: str = None,
                        metadata: Dict = None) -> Dict:
        """
        Log a Q&A conversation.
        
        Args:
            question: Student's question (transcribed).
            answer: AI's answer.
            video_id: ID of the video context (e.g., "Area_Circle").
            video_title: Title of the video.
            metadata: Additional metadata (tokens used, duration, etc.).
            
        Returns:
            The logged conversation entry.
        """
        conversation = {
            "id": self._generate_id(),
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "video_id": video_id or "unknown",
            "video_title": video_title or "Unknown Topic",
            "question": question,
            "answer": answer,
            "question_length": len(question.split()),
            "answer_length": len(answer.split()),
            "metadata": metadata or {}
        }
        
        # Save to main log
        self._append_to_log(self.main_log_file, conversation)
        
        # Save to daily log
        self._append_to_log(self.daily_log_file, conversation)
        
        print(f"✅ Conversation logged: {conversation['id']}")
        
        return conversation
    
    
    def get_all_conversations(self) -> List[Dict]:
        """Get all logged conversations."""
        return self._load_json(self.main_log_file)
    
    
    def get_conversations_by_date(self, date: str = None) -> List[Dict]:
        """
        Get conversations for a specific date.
        
        Args:
            date: Date in format "YYYY-MM-DD". If None, uses today.
            
        Returns:
            List of conversations for that date.
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        date_file = os.path.join(self.log_directory, f"conversations_{date}.json")
        
        if os.path.exists(date_file):
            return self._load_json(date_file)
        return []
    
    
    def get_conversations_by_video(self, video_id: str) -> List[Dict]:
        """
        Get all conversations for a specific video.
        
        Args:
            video_id: Video ID (e.g., "Area_Circle").
            
        Returns:
            List of conversations for that video.
        """
        all_convs = self.get_all_conversations()
        return [c for c in all_convs if c.get('video_id') == video_id]
    
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """
        Get the most recent conversations.
        
        Args:
            limit: Number of conversations to retrieve.
            
        Returns:
            List of recent conversations.
        """
        all_convs = self.get_all_conversations()
        return all_convs[-limit:] if all_convs else []
    
    
    def get_statistics(self) -> Dict:
        """
        Get learning statistics.
        
        Returns:
            Dictionary with statistics (total questions, topics covered, etc.).
        """
        all_convs = self.get_all_conversations()
        
        if not all_convs:
            return {
                "total_conversations": 0,
                "unique_videos": 0,
                "total_questions_asked": 0,
                "average_question_length": 0,
                "average_answer_length": 0,
                "first_conversation": None,
                "last_conversation": None
            }
        
        videos = set(c.get('video_id', 'unknown') for c in all_convs)
        question_lengths = [c.get('question_length', 0) for c in all_convs]
        answer_lengths = [c.get('answer_length', 0) for c in all_convs]
        
        return {
            "total_conversations": len(all_convs),
            "unique_videos": len(videos),
            "videos_studied": list(videos),
            "total_questions_asked": len(all_convs),
            "average_question_length": sum(question_lengths) / len(question_lengths),
            "average_answer_length": sum(answer_lengths) / len(answer_lengths),
            "first_conversation": all_convs[0].get('timestamp'),
            "last_conversation": all_convs[-1].get('timestamp')
        }
    
    
    def export_for_revision(self, output_file: str = None) -> str:
        """
        Export conversations in a readable format for revision.
        
        Args:
            output_file: Path to output file. If None, uses default.
            
        Returns:
            Path to the exported file.
        """
        if output_file is None:
            output_file = os.path.join(self.log_directory, "revision_notes.txt")
        
        all_convs = self.get_all_conversations()
        
        with open(output_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("REVISION NOTES - AI MATH TUTOR\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Q&A: {len(all_convs)}\n")
            f.write("=" * 70 + "\n\n")
            
            # Group by video
            by_video = {}
            for conv in all_convs:
                video_title = conv.get('video_title', 'Unknown')
                if video_title not in by_video:
                    by_video[video_title] = []
                by_video[video_title].append(conv)
            
            for video_title, conversations in by_video.items():
                f.write(f"\n{'=' * 70}\n")
                f.write(f"TOPIC: {video_title}\n")
                f.write(f"Questions: {len(conversations)}\n")
                f.write(f"{'=' * 70}\n\n")
                
                for i, conv in enumerate(conversations, 1):
                    f.write(f"Q{i}. {conv.get('question', 'N/A')}\n")
                    f.write(f"    [{conv.get('date', 'N/A')} {conv.get('time', 'N/A')}]\n\n")
                    f.write(f"A{i}. {conv.get('answer', 'N/A')}\n")
                    f.write(f"\n{'-' * 70}\n\n")
        
        print(f"✅ Revision notes exported to: {output_file}")
        return output_file
    
    
    # Helper methods
    def _generate_id(self) -> str:
        """Generate unique ID for conversation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"conv_{timestamp}"
    
    
    def _load_json(self, filepath: str) -> List[Dict]:
        """Load JSON file."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    
    def _save_json(self, filepath: str, data: List[Dict]):
        """Save JSON file."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    
    def _append_to_log(self, filepath: str, entry: Dict):
        """Append entry to log file."""
        data = self._load_json(filepath)
        data.append(entry)
        self._save_json(filepath, data)


# Simple test
if __name__ == "__main__":
    print("=" * 70)
    print("CONVERSATION LOGGER TEST")
    print("=" * 70)
    print()
    
    # Create logger
    logger = ConversationLogger()
    
    # Log a test conversation
    print("[Test 1] Logging a conversation...")
    conv = logger.log_conversation(
        question="Why is pi used in the area formula?",
        answer="Pi is used because it represents the constant ratio between a circle's circumference and diameter...",
        video_id="Area_Circle",
        video_title="Area of a Circle (Introduction to Pi)",
        metadata={"tokens_used": 150, "duration": 2.5}
    )
    print(f"Logged: {conv['id']}")
    print()
    
    # Get statistics
    print("[Test 2] Getting statistics...")
    stats = logger.get_statistics()
    print(f"Total conversations: {stats['total_conversations']}")
    print(f"Videos studied: {stats['videos_studied']}")
    print()
    
    # Export for revision
    print("[Test 3] Exporting revision notes...")
    revision_file = logger.export_for_revision()
    print(f"Exported to: {revision_file}")
    print()
    
    print("=" * 70)
    print("✅ Test complete!")

