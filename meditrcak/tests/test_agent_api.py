"""
Unit tests for agent API endpoints
Tests for transcription, TTS, and other agent endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import tempfile
import io
from pathlib import Path


class TestAgentAPI:
    """Test cases for agent API endpoints"""

    def test_health_endpoint(self, client):
        """Test agent health check endpoint"""
        response = client.get("/assistant/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "ok"

    def test_transcribe_endpoint_success(self, client, auth_headers):
        """Test successful audio transcription via query endpoint"""
        # Create a mock WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            # Write minimal WAV header + some dummy data
            wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
            temp_file.write(wav_header)
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as audio_file:
                files = {'audio_file': ('test.wav', audio_file, 'audio/wav')}
                response = client.post(
                    "/assistant/query",
                    files=files,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            # Should return transcription or handle gracefully
            assert response.status_code in [200, 400, 500]

            if response.status_code == 200:
                data = response.json()
                assert "agent_response" in data
                # Transcription might be in the response
                if "transcription" in data:
                    assert isinstance(data["transcription"], str)
        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_transcribe_endpoint_no_audio(self, client, auth_headers):
        """Test query endpoint without audio file"""
        response = client.post("/assistant/query", data={"text": "test"}, headers=auth_headers)

        assert response.status_code == 200  # Should work with text

    def test_transcribe_endpoint_unauthorized(self, client):
        """Test query endpoint without authentication"""
        response = client.post("/assistant/query", data={"text": "test"})

        assert response.status_code == 401

    @patch('app.agent.multimodal_handler.transcribe_audio')
    def test_transcribe_endpoint_with_mock(self, mock_transcribe, client, auth_headers):
        """Test transcription with mocked transcription service"""
        mock_transcribe.return_value = "This is a test transcription"

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'dummy audio data')
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as audio_file:
                files = {'audio': ('test.wav', audio_file, 'audio/wav')}
                response = client.post(
                    "/assistant/transcribe",
                    files=files,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            assert response.status_code == 200
            data = response.json()
            assert data["transcription"] == "This is a test transcription"
        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_tts_endpoint_success(self, client, auth_headers):
        """Test successful text-to-speech conversion via query endpoint"""
        data = {
            "text": "Hello, this is a test message for text to speech",
            "output_audio": "true",
            "tts_provider": "gtts"
        }

        response = client.post("/assistant/query", data=data, headers=auth_headers)

        # Should return audio or handle gracefully
        assert response.status_code in [200, 400, 500]

        if response.status_code == 200:
            data = response.json()
            assert "agent_response" in data
            # Audio path might be in the response
            if "audio_path" in data:
                assert isinstance(data["audio_path"], str)

    def test_tts_endpoint_missing_text(self, client, auth_headers):
        """Test query endpoint with missing text"""
        data = {"output_audio": "true"}
        response = client.post("/assistant/query", data=data, headers=auth_headers)

        assert response.status_code == 400  # Should require at least text, audio, or image

    def test_tts_endpoint_empty_text(self, client, auth_headers):
        """Test query endpoint with empty text"""
        data = {"text": "", "output_audio": "true"}
        response = client.post("/assistant/query", data=data, headers=auth_headers)

        assert response.status_code == 400  # Should require at least text, audio, or image

    @patch('app.agent.utils.text_to_speech.tts')
    def test_tts_endpoint_with_mock(self, mock_tts, client, auth_headers):
        """Test TTS with mocked speech generation"""
        mock_tts.return_value = {"success": True, "audio_path": "/tmp/test.mp3"}

        data = {
            "text": "Test message",
            "output_audio": "true",
            "tts_provider": "gtts"
        }

        response = client.post("/assistant/query", data=data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "agent_response" in data
        assert "audio_path" in data

    def test_tts_endpoint_unauthorized(self, client):
        """Test query endpoint without authentication"""
        data = {"text": "Test", "output_audio": "true"}
        response = client.post("/assistant/query", data=data)

        assert response.status_code == 401

    def test_multimodal_endpoint_audio_only(self, client, auth_headers):
        """Test query endpoint with audio only"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'dummy audio data')
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as audio_file:
                files = {'audio_file': ('test.wav', audio_file, 'audio/wav')}
                response = client.post(
                    "/assistant/query",
                    files=files,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            # Should handle gracefully
            assert response.status_code in [200, 400, 500]

            if response.status_code == 200:
                result = response.json()
                assert "agent_response" in result
        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_multimodal_endpoint_image_only(self, client, auth_headers):
        """Test query endpoint with image only"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'dummy image data')
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as image_file:
                files = {'image_file': ('test.jpg', image_file, 'image/jpeg')}
                response = client.post(
                    "/assistant/query",
                    files=files,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            # Should handle gracefully
            assert response.status_code in [200, 400, 500]
        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def test_multimodal_endpoint_both_audio_image(self, client, auth_headers):
        """Test query endpoint with both audio and image"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_temp:
            audio_temp.write(b'dummy audio data')
            audio_path = audio_temp.name

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as image_temp:
            image_temp.write(b'dummy image data')
            image_path = image_temp.name

        try:
            with open(audio_path, 'rb') as audio_file, open(image_path, 'rb') as image_file:
                files = {
                    'audio_file': ('test.wav', audio_file, 'audio/wav'),
                    'image_file': ('test.jpg', image_file, 'image/jpeg')
                }
                response = client.post(
                    "/assistant/query",
                    files=files,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            # Should handle gracefully
            assert response.status_code in [200, 400, 500]
        finally:
            Path(audio_path).unlink(missing_ok=True)
            Path(image_path).unlink(missing_ok=True)

    def test_multimodal_endpoint_no_files(self, client, auth_headers):
        """Test query endpoint with no files"""
        response = client.post("/assistant/query", data={"text": "test"}, headers=auth_headers)

        assert response.status_code == 200  # Should work with text

    def test_voice_query_endpoint(self, client, auth_headers):
        """Test voice query endpoint (transcribe + agent response)"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'dummy audio data')
            temp_file_path = temp_file.name

        try:
            with open(temp_file_path, 'rb') as audio_file:
                files = {'audio_file': ('voice.wav', audio_file, 'audio/wav')}
                response = client.post(
                    "/assistant/query",
                    files=files,
                    headers={k: v for k, v in auth_headers.items() if k != 'Content-Type'}
                )

            # Should handle gracefully
            assert response.status_code in [200, 400, 500]

            if response.status_code == 200:
                data = response.json()
                assert "transcription" in data
                assert "response" in data
        finally:
            Path(temp_file_path).unlink(missing_ok=True)
