# app/agent/tools/auth_tool.py
"""
Authentication Tool for AI Agent.
Authenticates users and sets the token for HTTP-based medication tools.
"""

import requests
from langchain.tools import tool
from typing import Optional
import logging

from app.agent.tools.http_client import set_agent_token, API_BASE_URL

logger = logging.getLogger(__name__)


@tool("authenticate_user", description="Authenticate a user with email and password to enable medication management features.")
def authenticate_user(email: str, password: str) -> str:
    """
    Authenticate the user and obtain an access token.
    This token is automatically set for subsequent medication tool calls.
    
    Args:
        email: User's email address
        password: User's password
    
    Returns:
        Success message or error description
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={"username": email, "password": password},  # OAuth2 expects form data
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                # Set the token for all HTTP-based tools
                set_agent_token(token)
                logger.info(f"User {email} authenticated successfully")
                return f"✅ Successfully authenticated! You can now access your medications, reminders, and adherence data."
            else:
                return "❌ Authentication failed: No token received."
        elif response.status_code == 401:
            return "❌ Invalid email or password. Please try again."
        else:
            return f"❌ Authentication failed: {response.text}"
            
    except requests.exceptions.Timeout:
        return "❌ Authentication timed out. Please try again."
    except requests.exceptions.RequestException as e:
        logger.error(f"Authentication error: {e}")
        return f"❌ Connection error: Unable to reach the server."


@tool("check_authentication", description="Check if the user is currently authenticated for medication access.")
def check_authentication() -> str:
    """
    Check if there's a valid authentication token set.
    
    Returns:
        Authentication status message
    """
    from app.agent.tools.http_client import get_agent_token
    
    token = get_agent_token()
    if token:
        return "✅ You are authenticated and can access medication features."
    else:
        return "⚠️ You are not authenticated. Please provide your email and password to access medication features."
