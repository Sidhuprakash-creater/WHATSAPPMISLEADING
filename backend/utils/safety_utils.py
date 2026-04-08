import re
import logging

logger = logging.getLogger(__name__)

# Synchronized with Mobile Filter List + PDF Dataset
BANNED_WORDS = [
    'badword', 'offensive', 'spam', 'scam', 'fake', 'abuse',
    'fuck', 'shit', 'asshole', 'bitch', 'dick', 'pussy',
    'chutiya', 'gaand', 'randi', 'harami', 'kamina', 'bhenchod', 'madarchod',
    'saala', 'kutte', 'suar', 'haramkhor', 'bakwas', 'jhooth', 'chor',
    
    # PDF Dataset terms
    'motherfucker', 'maaderchod', 'chinaal', 'rakhita', 'bollocks', 
    'bastard', 'bloody', 'cunt', 'slut', 'whore', 'scoundrel'
]

def is_safe_text(text: str) -> bool:
    """Returns True if no banned words are found. Uses aggressive substring matching."""
    if not text:
        return True
    
    content = text.lower()
    for word in BANNED_WORDS:
        # Aggressive substring check (no boundaries) to match mobile app logic
        if word.lower() in content:
            logger.warning(f"Safety violation detected: word '{word}' found in input.")
            return False
    return True

def sanitize_text(text: str) -> str:
    """Replaces banned words with asterisks using substring matching."""
    if not text:
        return text
    
    content = text
    for word in BANNED_WORDS:
        # Use regex to find substring case-insensitively
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        content = pattern.sub('*' * len(word), content)
    
    return content
