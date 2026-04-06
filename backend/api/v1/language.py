from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from analyzers.language_detector import detector

router = APIRouter(prefix="/language", tags=["Language"])

class LanguageRequest(BaseModel):
    text: str

class LanguageResponse(BaseModel):
    language: str
    confidence: float

@router.post("/detect-language", response_model=LanguageResponse)
async def detect_language(request: LanguageRequest):
    """
    Detect language of the provided text.
    Supported: English, Hindi, Hinglish, Odia.
    """
    if not request.text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    result = detector.detect(request.text)
    return LanguageResponse(
        language=result["language"],
        confidence=result["confidence"]
    )
