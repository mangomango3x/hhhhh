"""
Fact Checker Implementation
Integrates with Gemini 1.5 API for fact-checking functionality
"""

import os
import asyncio
import re
from typing import Dict, List, Optional
import google.generativeai as genai

from config.settings import FACT_CHECK_CONFIG
from utils.logger import get_logger

class FactChecker:
    """Handles fact-checking operations using Gemini 1.5 API"""

    def __init__(self):
        self.logger = get_logger(__name__)

        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=api_key)

        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=FACT_CHECK_CONFIG['model_name'],
            generation_config={
                "temperature": FACT_CHECK_CONFIG['temperature'],
                "max_output_tokens": FACT_CHECK_CONFIG['max_tokens'],
            }
        )

        self.logger.info("Fact checker initialized with Gemini 1.5")

    async def expose_claim(self, claim: str) -> Optional[dict]:
        """
        Expose/debunk a claim or validate it if debunking fails

        Args:
            claim: The claim to expose/debunk

        Returns:
            Dictionary with expose analysis results or None if failed
        """
        try:
            prompt = f"""
            You are a fact-checking expert specializing in exposing misinformation and debunking false claims.

            Your task is to analyze the following claim and either:
            1. DEBUNK it if it's false or misleading (provide strong evidence against it)
            2. SUPPORT it if it's actually true and cannot be debunked (provide evidence for it)

            Claim to analyze: "{claim}"

            Provide your response in this exact JSON format:
            {{
                "expose_type": "debunked" or "supported",
                "confidence": confidence_percentage_as_integer,
                "analysis": "detailed_analysis_explanation",
                "evidence": ["evidence_point_1", "evidence_point_2", "evidence_point_3"]
            }}

            Be thorough, factual, and cite reliable sources when possible.
            """

            response = await self._make_gemini_request(prompt)
            if response:
                # Parse JSON response
                import json
                try:
                    result = json.loads(response)
                    self.logger.info(f"Expose analysis completed for claim: {claim[:50]}...")
                    return result
                except json.JSONDecodeError:
                    # Fallback parsing if JSON is malformed
                    return self._parse_expose_response(response)

        except Exception as e:
            self.logger.error(f"Error in expose_claim: {e}")
            return None

    def _parse_expose_response(self, response: str) -> dict:
        """Parse expose response if JSON parsing fails"""
        try:
            # Extract key information using regex patterns
            import re

            expose_type = "unknown"
            if "debunked" in response.lower():
                expose_type = "debunked"
            elif "supported" in response.lower():
                expose_type = "supported"

            confidence_match = re.search(r'(\d+)%', response)
            confidence = int(confidence_match.group(1)) if confidence_match else 50

            return {
                "expose_type": expose_type,
                "confidence": confidence,
                "analysis": response[:500] + "..." if len(response) > 500 else response,
                "evidence": []
            }
        except Exception:
            return {
                "expose_type": "unknown",
                "confidence": 0,
                "analysis": "Failed to parse expose analysis",
                "evidence": []
            }

    async def check_claim(self, claim: str) -> Optional[Dict]:
        """
        Fact-check a claim using Gemini 1.5

        Args:
            claim: The claim to fact-check

        Returns:
            Dictionary containing fact-check results or None if failed
        """
        try:
            # Clean and validate the claim
            cleaned_claim = self._clean_claim(claim)
            if not cleaned_claim or len(cleaned_claim.strip()) < 10:
                return None

            # Generate the fact-check prompt
            prompt = self._create_fact_check_prompt(cleaned_claim)

            # Call Gemini API asynchronously
            response = await self._call_gemini_async(prompt)

            if response:
                # Parse the response
                result = self._parse_fact_check_response(response)
                return result

        except Exception as e:
            self.logger.error(f"Error fact-checking claim: {e}")
            return None

        return None

    def _clean_claim(self, claim: str) -> str:
        """Clean and preprocess the claim text"""
        # Remove Discord markdown and mentions
        claim = re.sub(r'<@[!&]?\d+>', '', claim)  # Remove mentions
        claim = re.sub(r'<#\d+>', '', claim)       # Remove channel references
        claim = re.sub(r'<:\w+:\d+>', '', claim)   # Remove custom emojis
        claim = re.sub(r'```[\s\S]*?```', '', claim)  # Remove code blocks
        claim = re.sub(r'`[^`]*`', '', claim)      # Remove inline code
        claim = re.sub(r'\*{1,2}([^*]*)\*{1,2}', r'\1', claim)  # Remove bold/italic
        claim = re.sub(r'_{1,2}([^_]*)_{1,2}', r'\1', claim)    # Remove underline
        claim = re.sub(r'~~([^~]*)~~', r'\1', claim)            # Remove strikethrough

        # Clean extra whitespace
        claim = ' '.join(claim.split())

        return claim.strip()

    def _create_fact_check_prompt(self, claim: str) -> str:
        """Create a comprehensive fact-checking prompt for Gemini"""
        prompt = f"""
You are an expert fact-checker. Please analyze the following claim thoroughly and provide a comprehensive fact-check.

CLAIM TO ANALYZE:
"{claim}"

Please provide your analysis in the following structured format:

ACCURACY: [True/Mostly True/Mixed/Mostly False/False/Insufficient Evidence]

CONFIDENCE: [0-100]% (How confident are you in this assessment?)

EXPLANATION: [Provide a detailed explanation of your fact-check, including:
- What aspects of the claim are accurate or inaccurate
- What evidence supports or contradicts the claim
- Any important context or nuances
- Why you reached this conclusion]

SOURCES: [List 2-4 reliable sources that support your analysis, if available. Format as brief descriptions rather than URLs]

IMPORTANT GUIDELINES:
- Be objective and evidence-based
- Consider multiple perspectives
- Distinguish between facts and opinions
- Note any missing context that affects accuracy
- If the claim is too vague or subjective to fact-check, indicate this
- For claims about current events, acknowledge if information may be rapidly evolving
- Be precise about what exactly is true or false in complex claims
"""
        return prompt

    async def _call_gemini_async(self, prompt: str) -> Optional[str]:
        """Make an asynchronous call to Gemini API"""
        try:
            # Run the synchronous API call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )

            if response and response.text:
                return response.text

        except Exception as e:
            self.logger.error(f"Gemini API call failed: {e}")

        return None

    def _parse_fact_check_response(self, response: str) -> Dict:
        """Parse the structured response from Gemini"""
        result = {
            'accuracy': 'Unknown',
            'confidence': 0,
            'explanation': '',
            'sources': []
        }

        try:
            # Extract accuracy
            accuracy_match = re.search(r'ACCURACY:\s*([^\n]+)', response, re.IGNORECASE)
            if accuracy_match:
                result['accuracy'] = accuracy_match.group(1).strip()

            # Extract confidence
            confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', response, re.IGNORECASE)
            if confidence_match:
                result['confidence'] = int(confidence_match.group(1))

            # Extract explanation
            explanation_match = re.search(
                r'EXPLANATION:\s*(.*?)(?=SOURCES:|$)', 
                response, 
                re.IGNORECASE | re.DOTALL
            )
            if explanation_match:
                explanation = explanation_match.group(1).strip()
                # Clean up the explanation
                explanation = re.sub(r'\n+', ' ', explanation)
                explanation = ' '.join(explanation.split())
                result['explanation'] = explanation

            # Extract sources
            sources_match = re.search(r'SOURCES:\s*(.*?)$', response, re.IGNORECASE | re.DOTALL)
            if sources_match:
                sources_text = sources_match.group(1).strip()
                # Split sources by lines and clean them
                sources = []
                for line in sources_text.split('\n'):
                    line = line.strip()
                    if line and not line.lower().startswith('important'):
                        # Remove bullet points and numbering
                        line = re.sub(r'^[-•*\d+.\s]+', '', line).strip()
                        if line:
                            sources.append(line)

                result['sources'] = sources[:4]  # Limit to 4 sources

        except Exception as e:
            self.logger.error(f"Error parsing fact-check response: {e}")
            # Return the raw response as explanation if parsing fails
            result['explanation'] = response[:500] + "..." if len(response) > 500 else response

        return result

    def _create_expose_prompt(self, claim: str) -> str:
        """Create a comprehensive expose prompt for Gemini"""
        prompt = f"""
You are an expert investigative analyst. Your task is to AGGRESSIVELY attempt to debunk and disprove the following claim. Try your absolute best to find flaws, contradictions, or evidence against it.

CLAIM TO EXPOSE:
"{claim}"

INSTRUCTIONS:
1. First, try your hardest to debunk this claim using:
   - Scientific evidence that contradicts it
   - Logical fallacies in the reasoning
   - Historical counterexamples
   - Expert consensus that opposes it
   - Data that disproves it
   - Any weaknesses or flaws you can find

2. If you CANNOT successfully debunk the claim (it appears to be well-supported), then switch to supporting it with strong evidence.

Please provide your analysis in the following structured format:

EXPOSE_TYPE: [DEBUNKED/SUPPORTED]

CONFIDENCE: [0-100]% (How confident are you in your analysis?)

ANALYSIS: [Provide a detailed analysis explaining:
- If DEBUNKED: All the ways this claim is false, misleading, or problematic
- If SUPPORTED: Why you couldn't debunk it and the strong evidence supporting it
- Key evidence and reasoning for your conclusion
- Important context or nuances]

EVIDENCE: [List 2-4 pieces of evidence that support your analysis]

IMPORTANT GUIDELINES:
- Be aggressive in your debunking attempt first
- Only support the claim if you genuinely cannot find credible ways to debunk it
- Be thorough and evidence-based
- Consider multiple angles of attack when debunking
- Distinguish between weak and strong evidence
- If the claim is partially true, focus on the problematic aspects for debunking
"""
        return prompt

    def _parse_expose_response_old(self, response: str) -> Dict:
        """Parse the structured expose response from Gemini"""
        result = {
            'expose_type': 'Unknown',
            'confidence': 0,
            'analysis': '',
            'evidence': []
        }

        try:
            # Extract expose type
            expose_match = re.search(r'EXPOSE_TYPE:\s*([^\n]+)', response, re.IGNORECASE)
            if expose_match:
                result['expose_type'] = expose_match.group(1).strip()

            # Extract confidence
            confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', response, re.IGNORECASE)
            if confidence_match:
                result['confidence'] = int(confidence_match.group(1))

            # Extract analysis
            analysis_match = re.search(
                r'ANALYSIS:\s*(.*?)(?=EVIDENCE:|$)', 
                response, 
                re.IGNORECASE | re.DOTALL
            )
            if analysis_match:
                analysis = analysis_match.group(1).strip()
                # Clean up the analysis
                analysis = re.sub(r'\n+', ' ', analysis)
                analysis = ' '.join(analysis.split())
                result['analysis'] = analysis

            # Extract evidence
            evidence_match = re.search(r'EVIDENCE:\s*(.*?)$', response, re.IGNORECASE | re.DOTALL)
            if evidence_match:
                evidence_text = evidence_match.group(1).strip()
                # Split evidence by lines and clean them
                evidence = []
                for line in evidence_text.split('\n'):
                    line = line.strip()
                    if line and not line.lower().startswith('important'):
                        # Remove bullet points and numbering
                        line = re.sub(r'^[-•*\d+.\s]+', '', line).strip()
                        if line:
                            evidence.append(line)

                result['evidence'] = evidence[:4]  # Limit to 4 pieces of evidence

        except Exception as e:
            self.logger.error(f"Error parsing expose response: {e}")
            # Return the raw response as analysis if parsing fails
            result['analysis'] = response[:500] + "..." if len(response) > 500 else response

        return result

    async def check_url_claim(self, url: str) -> Optional[Dict]:
        """
        Fact-check a claim from a URL (future enhancement)

        Args:
            url: URL to analyze

        Returns:
            Dictionary containing fact-check results or None if failed
        """
        # This is a placeholder for future URL analysis functionality
        # Would require web scraping capabilities
        self.logger.info(f"URL fact-checking not yet implemented: {url}")
        return None

    async def _make_gemini_request(self, prompt: str) -> Optional[str]:
        """
        Make a request to Gemini API

        Args:
            prompt: The prompt to send to Gemini

        Returns:
            Response text or None if failed
        """
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Gemini API request failed: {e}")
            return None