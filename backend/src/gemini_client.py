"""Gemini API client with support for both AI Studio and Vertex AI."""

import os
import time
from typing import Optional
from pathlib import Path

from .utils import log_message


class GeminiClientError(Exception):
    """Raised when Gemini API call fails."""
    pass


class GeminiClient:
    """
    Unified Gemini client supporting both AI Studio and Vertex AI.
    """
    
    def __init__(
        self,
        provider: str = "studio",
        model_name: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        auth_file: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 8192,
    ):
        """
        Initialize Gemini client.
        
        Args:
            provider: "studio" for AI Studio or "vertex" for Vertex AI
            model_name: Model to use (e.g., gemini-2.5-flash)
            api_key: API key for AI Studio
            project_id: GCP project ID for Vertex AI
            location: GCP region for Vertex AI
            auth_file: Path to service account JSON for Vertex AI
            temperature: Generation temperature
            max_output_tokens: Maximum output tokens
        """
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        
        self._model = None
        self._system_instruction = None
        
        if provider == "studio":
            self._init_studio(api_key)
        elif provider == "vertex":
            self._init_vertex(project_id, location, auth_file)
        else:
            raise GeminiClientError(f"Unknown provider: {provider}")
    
    def _init_studio(self, api_key: Optional[str]):
        """Initialize Google AI Studio client."""
        import google.generativeai as genai
        
        # Get API key from argument, env var, or .env file
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            # Try loading from .env file
            try:
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.environ.get("GEMINI_API_KEY")
            except ImportError:
                pass
        
        if not api_key:
            raise GeminiClientError(
                "API key not found. Set GEMINI_API_KEY environment variable "
                "or pass --api-key argument."
            )
        
        genai.configure(api_key=api_key)
        log_message(f"Initialized AI Studio client with model: {self.model_name}")
        
        self._genai = genai
    
    def _init_vertex(
        self,
        project_id: Optional[str],
        location: str,
        auth_file: Optional[str]
    ):
        """Initialize Vertex AI client."""
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        if not project_id:
            project_id = os.environ.get("VERTEX_PROJECT_ID")
        if not project_id:
            raise GeminiClientError("Project ID required for Vertex AI")
        
        if auth_file:
            if not Path(auth_file).exists():
                raise GeminiClientError(f"Auth file not found: {auth_file}")
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = auth_file
            log_message(f"Using service account from: {auth_file}")
        
        vertexai.init(project=project_id, location=location)
        log_message(f"Initialized Vertex AI: project={project_id}, location={location}")
        
        self._vertexai = vertexai
        self._GenerativeModel = GenerativeModel
    
    def set_system_instruction(self, instruction: str):
        """Set system instruction for the model."""
        self._system_instruction = instruction
        
        if self.provider == "studio":
            self._model = self._genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=instruction,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_output_tokens,
                }
            )
        else:
            self._model = self._GenerativeModel(
                model_name=self.model_name,
                system_instruction=instruction,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_output_tokens,
                }
            )
    
    def generate(
        self,
        prompt: str,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ) -> str:
        """
        Generate response from the model.
        
        Args:
            prompt: User prompt
            max_retries: Maximum retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
            
        Returns:
            Generated text
        """
        if self._model is None:
            raise GeminiClientError("System instruction not set. Call set_system_instruction first.")
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self._model.generate_content(prompt)
                
                # Extract text from response
                if hasattr(response, 'text'):
                    return response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    return response.candidates[0].content.parts[0].text
                else:
                    raise GeminiClientError("Unexpected response format")
                    
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check for rate limiting
                if 'rate' in error_msg or 'quota' in error_msg or '429' in error_msg:
                    wait_time = retry_delay * (2 ** attempt)
                    log_message(f"Rate limited. Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                # Check for transient errors
                if 'timeout' in error_msg or '503' in error_msg or '500' in error_msg:
                    wait_time = retry_delay * (2 ** attempt)
                    log_message(f"Transient error. Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                # Non-retryable error
                raise GeminiClientError(f"API error: {e}")
        
        raise GeminiClientError(f"Max retries exceeded. Last error: {last_error}")
