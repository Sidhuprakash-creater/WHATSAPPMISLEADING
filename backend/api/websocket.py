"""
WebSocket — Real-time analysis progress streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()


@router.websocket("/ws/analysis/{analysis_id}")
async def analysis_progress(websocket: WebSocket, analysis_id: str):
    """
    Stream real-time analysis progress to frontend.
    Sends steps: checking_cache → running_ml → running_llm → computing_score → done
    """
    await websocket.accept()
    
    try:
        # These steps are sent as the analysis progresses
        steps = [
            {"step": "checking_cache", "message": "Checking cache...", "progress": 10},
            {"step": "running_ml", "message": "Running ML model...", "progress": 30},
            {"step": "running_analyzers", "message": "Running analyzers...", "progress": 50},
            {"step": "running_llm", "message": "AI reasoning...", "progress": 70},
            {"step": "computing_score", "message": "Computing final score...", "progress": 90},
            {"step": "done", "message": "Analysis complete!", "progress": 100},
        ]
        
        # Wait for start signal from client
        data = await websocket.receive_text()
        
        # In production, this would be driven by actual analysis progress
        # For now, send progress steps as analysis runs
        for step in steps:
            await websocket.send_text(json.dumps(step))
        
    except WebSocketDisconnect:
        pass
