
# ============================================================================
# INTENT CLASSIFICATION
# ============================================================================

# Common greetings and casual phrases
GREETINGS = {
    "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
    "howdy", "greetings", "sup", "what's up", "yo", "hiya"
}

CASUAL_PHRASES = {
    "how are you", "how's it going", "how are you doing", "what's new",
    "nice to meet you", "thanks", "thank you", "bye", "goodbye", "see you"
}


def classify_intent(message: str) -> str:
    """
    Classify user message intent.
    
    Args:
        message: User's message text
        
    Returns:
        Intent type: 'greeting', 'casual', or 'medical'
    """
    text = message.lower().strip()
    
    # Check for exact greeting match
    if text in GREETINGS:
        return "greeting"
    
    # Check for casual phrases
    for phrase in CASUAL_PHRASES:
        if phrase in text:
            return "casual"
    
    # Check for very short messages (likely greetings)
    if len(text.split()) <= 2 and text in GREETINGS:
        return "greeting"
    
    # Default to medical intent
    return "medical"


def get_quick_response(intent: str, user_name: str = None) -> str:
    """
    Generate quick response for greetings/casual messages.
    
    Args:
        intent: Intent type ('greeting' or 'casual')
        user_name: Optional user name for personalization
        
    Returns:
        Appropriate response string
    """
    name = user_name if user_name else "there"
    
    if intent == "greeting":
        return f"Hello {name}! I'm MediBot, your medical assistant. How can I help you today? You can ask about your medications, health conditions, or general medical questions."
    
    elif intent == "casual":
        return "I'm here to help with your health and medical questions. What would you like to know?"
    
    return None
