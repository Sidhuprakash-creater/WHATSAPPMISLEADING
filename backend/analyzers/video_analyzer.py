"""
Video Analyzer — Frame extraction + image analysis pipeline
Extracts key frames from video and runs image analysis on each
"""
import logging

logger = logging.getLogger(__name__)


async def analyze(file_url: str) -> dict:
    """
    Analyze video by extracting frames and running image analysis.
    For hackathon: simplified version that analyzes video thumbnail/first frame.
    """
    try:
        from analyzers import image_analyzer
        
        # For hackathon, analyze the video URL as an image
        # In production, use OpenCV to extract frames:
        #   cap = cv2.VideoCapture(file_url)
        #   frames = extract_key_frames(cap, num_frames=3)
        #   results = [await image_analyzer.analyze(frame) for frame in frames]
        
        result = await image_analyzer.analyze(file_url)
        result["content_type"] = "video"
        result["details"] = f"Video analysis (frame sample): {result.get('details', 'N/A')}"
        
        return result
        
    except Exception as e:
        logger.error(f"Video analysis failed: {e}")
        return {
            "analyzed": False,
            "reason": str(e),
            "score": 0,
            "content_type": "video",
        }
