# app/agent/tools/http_client.py
"""
Authenticated HTTP Client for Agent Tools.
All agent tools should use this client to call FastAPI endpoints.
"""

import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# API Base URL - should match your FastAPI server
API_BASE_URL = "http://localhost:8000"


class AgentHTTPClient:
    """
    HTTP client for agent tools with JWT authentication.
    
    Usage:
        client = AgentHTTPClient(token="eyJ...")
        data = client.get("/medications/patients/5/medications")
    """
    
    def __init__(self, token: str, base_url: str = API_BASE_URL):
        self.token = token
        self.base_url = base_url
        self.timeout = 30
    
    def _headers(self) -> Dict[str, str]:
        """Get headers with JWT authentication."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated GET request."""
        try:
            url = f"{self.base_url}{path}"
            logger.debug(f"GET {url}")
            
            response = requests.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if e.response.status_code == 401:
                return {"error": "Authentication failed. Please log in again."}
            elif e.response.status_code == 403:
                return {"error": "You don't have permission to access this resource."}
            elif e.response.status_code == 404:
                return {"error": "Resource not found."}
            return {"error": f"Request failed: {str(e)}"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {"error": f"Connection error: {str(e)}"}
    
    def post(self, path: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated POST request."""
        try:
            url = f"{self.base_url}{path}"
            logger.debug(f"POST {url}")
            
            response = requests.post(
                url,
                headers=self._headers(),
                json=payload or {},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if e.response.status_code == 401:
                return {"error": "Authentication failed. Please log in again."}
            elif e.response.status_code == 422:
                return {"error": "Invalid data provided."}
            return {"error": f"Request failed: {str(e)}"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {"error": f"Connection error: {str(e)}"}
    
    def put(self, path: str, payload: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated PUT request."""
        try:
            url = f"{self.base_url}{path}"
            logger.debug(f"PUT {url}")
            
            response = requests.put(
                url,
                headers=self._headers(),
                json=payload or {},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {"error": f"Request failed: {str(e)}"}
    
    def delete(self, path: str) -> Dict[str, Any]:
        """Make authenticated DELETE request."""
        try:
            url = f"{self.base_url}{path}"
            logger.debug(f"DELETE {url}")
            
            response = requests.delete(
                url,
                headers=self._headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return {"success": True}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {"error": f"Request failed: {str(e)}"}


# Token storage for the current session
_current_token: Optional[str] = None
_current_user_id: Optional[int] = None


def set_agent_token(token: str):
    """Set the JWT token for agent HTTP calls."""
    global _current_token
    _current_token = token
    logger.info("Agent token set")


def set_agent_user_id(user_id: int):
    """Set the user ID for agent tools."""
    global _current_user_id
    _current_user_id = user_id
    logger.info(f"Agent user_id set: {user_id}")


def get_agent_token() -> Optional[str]:
    """Get the current JWT token."""
    return _current_token


def get_agent_user_id() -> Optional[int]:
    """Get the current user ID."""
    return _current_user_id


def get_client() -> AgentHTTPClient:
    """Get an authenticated HTTP client for the current session."""
    token = get_agent_token()
    if not token:
        raise ValueError("No authentication token set. Call set_agent_token first.")
    return AgentHTTPClient(token=token)
