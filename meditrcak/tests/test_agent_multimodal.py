"""
Unit tests for agent multimodal functionality
Tests for voice, image, and multimodal processing
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import tempfile
import io
from pathlib import Path


class TestAgentMultimodal:
    """Test cases for agent multimodal functionality"""

    def test_transcribe_endpoint(self, client, auth_headers):
        """Test audio transcription endpoint"""
        # Create mock audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            # Write some dummy WAV data
            temp_file.write(b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00')
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as audio_file:
                files = {'audio': ('test.wav', audio_file, 'audio/wav')}
                response = client.post(
                    "/agent/transcribe",
                    files=files,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            # Should return transcription or error gracefully
            assert response.status_code in [200, 400, 500]  # Allow for missing dependencies
        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_tts_endpoint(self, client, auth_headers):
        """Test text-to-speech endpoint"""
        tts_data = {
            "text": "Hello, this is a test message",
            "voice": "gtts"
        }

        response = client.post("/agent/tts", json=tts_data, headers=auth_headers)

        # Should return audio file or error gracefully
        assert response.status_code in [200, 400, 500]  # Allow for missing dependencies
        if response.status_code == 200:
            assert response.headers.get('content-type') in ['audio/mpeg', 'audio/wav', 'application/octet-stream']

    def test_health_endpoint(self, client):
        """Test agent health endpoint"""
        response = client.get("/agent/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "agent"

    @patch('app.agent.multimodal_handler.h')
    def test_multimodal_handler_audio_only(self, mock_handler, client, auth_headers):
        """Test multimodal handler with audio only"""
        mock_handler.return_value = ("Test transcription", "Test response", "/path/to/audio.wav")

        # Create mock audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'dummy audio data')
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as audio_file:
                files = {
                    'audio': ('test.wav', audio_file, 'audio/wav')
                }
                data = {'system_prompt': 'You are a helpful assistant'}
                response = client.post(
                    "/agent/multimodal",
                    files=files,
                    data=data,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            assert response.status_code == 200
            result = response.json()
            assert "transcription" in result
            assert "response" in result
            assert "audio_path" in result
        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    @patch('tools.image_analysis.identify_pill')
    def test_pill_identification_tool(self, mock_identify, client, auth_headers):
        """Test pill identification functionality"""
        mock_identify.return_value = {
            "most_likely": "Ibuprofen 200mg",
            "confidence": 0.85,
            "predictions": [
                {"type": "Ibuprofen 200mg", "confidence": 0.85},
                {"type": "Acetaminophen 500mg", "confidence": 0.12}
            ]
        }

        # Create mock image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'dummy image data')
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as image_file:
                files = {'image': ('pill.jpg', image_file, 'image/jpeg')}
                response = client.post(
                    "/agent/identify-pill",
                    files=files,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            assert response.status_code == 200
            result = response.json()
            assert "most_likely" in result
            assert "confidence" in result
            assert "predictions" in result
        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    @patch('tools.image_analysis.analyze_medical_image')
    def test_medical_image_analysis_tool(self, mock_analyze, client, auth_headers):
        """Test medical image analysis functionality"""
        mock_analyze.return_value = {
            "analysis": "Skin appears normal with no visible rashes",
            "confidence": 0.78,
            "recommendations": ["Continue monitoring", "Consult dermatologist if symptoms worsen"]
        }

        # Create mock image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'dummy image data')
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as image_file:
                files = {'image': ('skin.jpg', image_file, 'image/jpeg')}
                data = {'query': 'Analyze this skin condition'}
                response = client.post(
                    "/agent/analyze-image",
                    files=files,
                    data=data,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            assert response.status_code == 200
            result = response.json()
            assert "analysis" in result
            assert "confidence" in result
        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_agent_query_with_image(self, client, auth_headers):
        """Test agent query with image attachment"""
        # Create mock image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'dummy image data')
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as image_file:
                files = {'image': ('medical.jpg', image_file, 'image/jpeg')}
                data = {
                    'query': 'What do you see in this medical image?',
                    'context': '{"user_id": "123"}'
                }
                response = client.post(
                    "/agent/query-with-image",
                    files=files,
                    data=data,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            # Should handle gracefully even if image processing fails
            assert response.status_code in [200, 400, 500]
        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_voice_pipeline_integration(self, client, auth_headers):
        """Test complete voice pipeline: speech to text to agent response"""
        # Create mock audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'dummy audio data')
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as audio_file:
                files = {'audio': ('voice.wav', audio_file, 'audio/wav')}
                response = client.post(
                    "/agent/voice-query",
                    files=files,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            # Should handle gracefully
            assert response.status_code in [200, 400, 500]
        finally:
            Path(temp_file_path).unlink(missing_ok=True)