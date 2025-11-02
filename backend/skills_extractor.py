from typing import List, Dict
import json
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()


class SkillsExtractor:
    """Skills extractor that supports either OpenAI-style clients or Google's
    Generative (Gemini) REST endpoint. If no LLM key is present the class will
    fall back to a lightweight heuristic extractor so the backend still works
    during development.
    """

    def __init__(self):
        # Prefer Gemini/Google key if provided, otherwise fall back to OpenAI
        self.gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')

        # Configurable Gemini endpoint (allow override)
        self.gemini_url = os.getenv('GEMINI_URL') or (
            'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'
        )

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini-like REST endpoint using API key auth (simple HTTP key).
        This attempts a best-effort call to the Google Generative Language
        endpoint. If it fails, the caller will handle the fallback.
        """
        if not self.gemini_key:
            raise RuntimeError('No Gemini/Google API key configured')

        # Print request details for debugging
        print(f"Calling Gemini API at: {self.gemini_url}")
        
        headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': self.gemini_key
        }
        
        body = {
            'contents': [
                {'parts': [{'text': prompt}]}
            ],
            'safetySettings': [
                {
                    'category': 'HARM_CATEGORY_DANGEROUS',
                    'threshold': 'BLOCK_NONE'
                }
            ]
        }
        # Log the request body for debugging
        print(f"Request body: {json.dumps(body, indent=2)}")

        resp = requests.post(self.gemini_url, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Print response for debugging
        print(f"Gemini API response: {json.dumps(data, indent=2)}")
        
        # Try to extract generated text from Gemini response format
        if isinstance(data, dict):
            # New Gemini Pro format
            if 'candidates' in data and data['candidates']:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if parts and 'text' in parts[0]:
                        return parts[0]['text']
            
            # Legacy/alternative formats
            if 'output' in data and isinstance(data['output'], list) and len(data['output']) > 0:
                return ''.join([o.get('content', '') for o in data['output'] if isinstance(o, dict)])

        # Fallback: return full JSON as string
        return json.dumps(data)

    def _heuristic_extract(self, job_description: str) -> List[Dict]:
        """Simple heuristic skill extractor used when no LLM is available.
        Returns a list of dicts: {'name': str, 'category': 'technical'|'soft'}
        """
        # Look for common skill tokens (small set — keeps responses useful)
        tokens = re.findall(r"[A-Za-z+#\.\-]{2,}", job_description.lower())
        common_skills = {
            'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'azure',
            'docker', 'kubernetes', 'html', 'css', 'git', 'django', 'flask'
        }
        found = set(t for t in common_skills if any(t in token for token in tokens))

        # Return as skill dicts defaulting to technical
        return [{'name': s, 'category': 'technical'} for s in sorted(found)]

    def extract_skills(self, job_description: str) -> List[Dict]:
        """Extract skills from job description using Gemini if configured,
        otherwise fallback to a heuristic extractor.
        The function returns a list of skill objects with 'name' and 'category'.
        """
        # If Gemini key is present, attempt to call it
        if self.gemini_key:
            prompt = (
                "You are a skills analysis expert. Extract technical and soft skills "
                "from the following job description. Provide output as a JSON object:"
                " {\"skills\": [{\"name\": ..., \"category\": \"technical\"|\"soft\"}, ...] }\n"
                "Only output valid JSON and nothing else. Job description:\n\n"
                f"{job_description}"
            )
            try:
                generated = self._call_gemini(prompt)
                # The model should output JSON; try to parse it
                skills_data = json.loads(generated)
                return skills_data.get('skills', []) if isinstance(skills_data, dict) else []
            except Exception as e:
                print(f"Gemini call failed, falling back to heuristic extractor: {e}")
                return self._heuristic_extract(job_description)

        # If OpenAI key exists, try to use the OpenAI-compatible client if installed
        if self.openai_key:
            try:
                # Lazy import to avoid hard dependency when using Gemini
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": (
                            "You are a skills analysis expert. Extract technical and soft skills "
                            "from the following job description and return JSON: {\"skills\": [...] }"
                        )},
                        {"role": "user", "content": job_description}
                    ],
                    response_format={"type": "json_object"}
                )
                skills_data = json.loads(response.choices[0].message.content)
                return skills_data.get('skills', [])
            except Exception as e:
                print(f"OpenAI client failed, falling back to heuristic: {e}")
                return self._heuristic_extract(job_description)

        # No LLM key present — return heuristic extraction so app remains functional
        return self._heuristic_extract(job_description)

    def explain_skill(self, skill: str) -> str:
        """Generate a short, neurodivergent-friendly explanation for a skill.
        Uses Gemini if available, otherwise returns a concise template.
        """
        if self.gemini_key:
            prompt = (
                "Explain this technical skill in simple, concrete terms with a short "
                "analogy and one practical example. Keep it concise. Skill: " + skill
            )
            try:
                generated = self._call_gemini(prompt)
                return generated.strip()
            except Exception as e:
                print(f"Gemini explain failed, fallback: {e}")

        if self.openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": (
                            "Explain technical concepts simply, use analogies, be concise"
                        )},
                        {"role": "user", "content": f"Explain this skill: {skill}"}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI explain failed, fallback: {e}")

        # Simple template fallback
        return f"{skill}: A practical skill often used in software work. Try searching examples online to learn step-by-step." 