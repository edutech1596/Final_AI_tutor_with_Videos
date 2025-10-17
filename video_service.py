"""
Video Management Service for Unified Learning Platform
Handles video library, metadata, and progress tracking
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

class VideoService:
    def __init__(self):
        self.video_base_path = "/Users/apple/manim_with_voice/media/videos"
        self.video_library = []
        self.user_progress = {}
        self.load_video_library()
    
    def load_video_library(self):
        """Load all available videos from the manim_with_voice directory"""
        try:
            # Define video categories and their descriptions
            categories = {
                "01_hello_manim_voice": {
                    "title": "Hello Manim",
                    "description": "Introduction to Manim and basic concepts",
                    "order": 1
                },
                "02_basic_shapes_voice": {
                    "title": "Basic Shapes",
                    "description": "Learn about circles, squares, lines, and basic geometric shapes",
                    "order": 2
                },
                "03_text_basics_voice": {
                    "title": "Text Basics",
                    "description": "Working with text, formatting, and positioning",
                    "order": 3
                },
                "04_colors_voice": {
                    "title": "Colors",
                    "description": "Understanding colors, gradients, and visual effects",
                    "order": 4
                },
                "05_create_animations_voice": {
                    "title": "Create Animations",
                    "description": "Creating and managing animations",
                    "order": 5
                },
                "06_transform_animations_voice": {
                    "title": "Transform Animations",
                    "description": "Transforming objects and creating smooth transitions",
                    "order": 6
                },
                "07_movement_voice": {
                    "title": "Movement",
                    "description": "Moving objects and creating dynamic scenes",
                    "order": 7
                },
                "08_timing_voice": {
                    "title": "Timing",
                    "description": "Controlling animation timing and sequences",
                    "order": 8
                },
                "09_positioning_voice": {
                    "title": "Positioning",
                    "description": "Precise object positioning and alignment",
                    "order": 9
                },
                "10_multiple_objects_voice": {
                    "title": "Multiple Objects",
                    "description": "Working with multiple objects and complex scenes",
                    "order": 10
                },
                "11_groups_voice": {
                    "title": "Groups",
                    "description": "Grouping objects and managing collections",
                    "order": 11
                },
                "12_equations_voice": {
                    "title": "Equations",
                    "description": "Mathematical equations and LaTeX rendering",
                    "order": 12
                }
            }
            
            self.video_library = []
            
            # Scan the video directory
            if os.path.exists(self.video_base_path):
                for category_dir in sorted(os.listdir(self.video_base_path)):
                    if category_dir.startswith('_') or not os.path.isdir(os.path.join(self.video_base_path, category_dir)):
                        continue
                    
                    category_info = categories.get(category_dir, {
                        "title": category_dir.replace('_', ' ').title(),
                        "description": f"Educational content from {category_dir}",
                        "order": 999
                    })
                    
                    category_path = os.path.join(self.video_base_path, category_dir, "480p15")
                    if os.path.exists(category_path):
                        # Find all MP4 files in this category
                        for file in os.listdir(category_path):
                            if file.endswith('.mp4') and not file.startswith('partial_'):
                                video_id = f"{category_dir}_{file.replace('.mp4', '')}"
                                video_url = f"/videos/{category_dir}/480p15/{file}"
                                
                                # Get video duration (simplified - in real implementation, use ffprobe)
                                duration = self.estimate_duration(file)
                                
                                video_info = {
                                    "id": video_id,
                                    "title": file.replace('Voice.mp4', '').replace('_', ' '),
                                    "description": f"{category_info['description']} - {file.replace('Voice.mp4', '')}",
                                    "url": video_url,
                                    "category": category_info['title'],
                                    "category_order": category_info['order'],
                                    "duration": duration,
                                    "thumbnail": f"/videos/{category_dir}/480p15/{file.replace('.mp4', '_thumb.jpg')}",
                                    "subtitle_url": f"/videos/{category_dir}/480p15/{file.replace('.mp4', '.srt')}",
                                    "audio_url": f"/videos/{category_dir}/480p15/{file.replace('.mp4', '.wav')}"
                                }
                                
                                self.video_library.append(video_info)
            
            # Sort by category order and title
            self.video_library.sort(key=lambda x: (x['category_order'], x['title']))
            
            print(f"[✅] Loaded {len(self.video_library)} videos from video library")
            
        except Exception as e:
            print(f"[❌] Error loading video library: {e}")
            self.video_library = []
    
    def estimate_duration(self, filename: str) -> str:
        """Estimate video duration based on filename patterns"""
        # This is a simplified estimation - in production, use ffprobe
        duration_map = {
            'HelloManim': '2:30',
            'ColorfulCircle': '1:45',
            'MultipleAnimations': '3:15',
            'Lines': '2:00',
            'MoreShapes': '2:30',
            'ShapeGallery': '4:00',
            'ShapeProperties': '2:15',
            'SimpleText': '1:30',
            'TextFormatting': '2:45',
            'TextPositioning': '2:15',
            'TextWithShapes': '3:00',
            'ColorBasics': '2:00',
            'ColorShades': '2:30',
            'CustomColors': '2:15',
            'GradientColors': '2:45',
            'CreateMethods': '2:30',
            'MoreCreateAnimations': '3:00',
            'UncreateAnimations': '2:15',
            'WriteAnimation': '2:45',
            'BasicTransform': '2:30',
            'ReplacementTransformExample': '3:15',
            'TextTransform': '2:45',
            'TransformMatchingShapesExample': '3:30',
            'MoveToPosition': '2:15',
            'NextToPosition': '2:30',
            'RotationMovement': '2:45',
            'ShiftMovement': '2:15',
            'ToEdgeMovement': '2:30',
            'RunTime': '2:00',
            'SequentialTiming': '2:45',
            'SimultaneousTiming': '2:30',
            'WaitTiming': '2:15',
            'RateFunction': '3:00',
            'CenterAndShift': '2:15',
            'AlignmentBasics': '2:30',
            'ArrangeInRow': '2:15',
            'ArrangeInGrid': '2:45',
            'MultipleCircles': '2:30',
            'MultipleAnimations': '3:15',
            'CopyingObjects': '2:15',
            'ListComprehension': '2:45',
            'BasicGroup': '2:15',
            'GroupOperations': '2:45',
            'GroupWithText': '2:30',
            'NestedGroups': '3:00',
            'AddToGroup': '2:15',
            'SimpleEquation': '2:00',
            'ColoredEquation': '2:15',
            'EquationArray': '2:45',
            'EquationWithText': '2:30',
            'TransformEquation': '2:45',
            'MultipleEquations': '3:15'
        }
        
        for pattern, duration in duration_map.items():
            if pattern in filename:
                return duration
        
        return "2:30"  # Default duration
    
    def get_video_library(self) -> List[Dict[str, Any]]:
        """Get the complete video library"""
        return self.video_library
    
    def get_video_by_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific video by ID"""
        for video in self.video_library:
            if video['id'] == video_id:
                return video
        return None
    
    def get_videos_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get videos filtered by category"""
        return [video for video in self.video_library if video['category'] == category]
    
    def get_categories(self) -> List[str]:
        """Get all available categories"""
        categories = set(video['category'] for video in self.video_library)
        return sorted(categories)
    
    def update_user_progress(self, user_id: str, video_id: str, progress: Dict[str, Any]):
        """Update user progress for a specific video"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        
        self.user_progress[user_id][video_id] = {
            **progress,
            'last_updated': time.time()
        }
    
    def get_user_progress(self, user_id: str, video_id: str = None) -> Dict[str, Any]:
        """Get user progress for a specific video or all videos"""
        if user_id not in self.user_progress:
            return {}
        
        if video_id:
            return self.user_progress[user_id].get(video_id, {})
        else:
            return self.user_progress[user_id]
    
    def get_video_context(self, video_id: str) -> str:
        """Get contextual information about a video for AI responses"""
        video = self.get_video_by_id(video_id)
        if not video:
            return "General math tutoring context"
        
        context = f"""
        Current Video Context:
        - Title: {video['title']}
        - Category: {video['category']}
        - Description: {video['description']}
        
        The student is currently watching a {video['category']} video about {video['title']}.
        This video covers {video['description']}.
        """
        
        return context.strip()
    
    def search_videos(self, query: str) -> List[Dict[str, Any]]:
        """Search videos by title or description"""
        query_lower = query.lower()
        results = []
        
        for video in self.video_library:
            if (query_lower in video['title'].lower() or 
                query_lower in video['description'].lower() or
                query_lower in video['category'].lower()):
                results.append(video)
        
        return results

# Global video service instance
video_service = VideoService()
