import os
import re
import json
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class CareerBrain:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.1-8b-instant"

    def _get_next_question(self, s):
        """Determines the next logical step based on missing data."""
        if not s.get('name'):
            return "To get started, what's your name?"
        if not s.get('grade'):
            return f"Nice to meet you, {s['name']}! Which grade are you in?"
        if not s.get('board'):
            return "And which school board are you under (e.g., CBSE, ICSE, IB)?"
        if not s.get('interests'):
            return "What subjects do you enjoy most, or what do you find yourself doing in your free time?"
        if not s.get('strengths'):
            return "What would you say are your natural strengths? (e.g., leadership, technical logic, empathy, creativity?)"
        
        return "I've gathered some great insights! Would you like to see your personalized career discovery report?"

    @st.cache_data
    def cached_llm_extract(_self, user_input):
        """Uses LLM to generically extract interests/strengths with caching to save memory."""
        prompt = f"""
        Analyze the user input and extract:
        1. Interests (hobbies/subjects)
        2. Strengths (skills/traits)
        Return ONLY a JSON object: {{"interests": [], "strengths": []}}. 
        If none found, return empty lists.
        Input: "{user_input}"
        """
        try:
            chat_completion = _self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a data extractor. Output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model=_self.model,
                response_format={"type": "json_object"}
            )
            return json.loads(chat_completion.choices[0].message.content)
        except Exception:
            return {"interests": [], "strengths": []}

    def get_response(self, user_input, scribe_data):
        ui_raw = user_input or ""
        ui = ui_raw.lower()
        local_update = {}

        # 1. Regex for structured data (Name, Grade, Board)
        if not scribe_data.get('name'):
            name_match = re.search(r"(?:my name is|i'm|i am|call me)\s+([A-Z][a-z]+)", ui_raw, re.I)
            if name_match:
                local_update['name'] = name_match.group(1).capitalize()
        
        if not scribe_data.get('grade'):
            grade_match = re.search(r"(\d{1,2})", ui)
            if grade_match and 1 <= int(grade_match.group(1)) <= 12:
                local_update['grade'] = grade_match.group(1)

        if not scribe_data.get('board'):
            board_match = re.search(r"\b(cbse|icse|ib|igcse|state|isc)\b", ui)
            if board_match:
                local_update['board'] = board_match.group(1).upper()

        # 2. LLM for Unstructured data (Interests, Strengths)
        if scribe_data.get('board') and (not scribe_data.get('interests') or not scribe_data.get('strengths')):
            extracted = self.cached_llm_extract(ui_raw)
            if extracted.get('interests'):
                local_update['interests'] = list(set(scribe_data.get('interests', []) + extracted['interests']))
            if extracted.get('strengths'):
                local_update['strengths'] = list(set(scribe_data.get('strengths', []) + extracted['strengths']))

        # 3. Final State Sync
        current_state = {**scribe_data, **local_update}
        next_q = self._get_next_question(current_state)

        # Prevent repeating the same question if no new info was found
        if not local_update and user_input:
            msg = f"I didn't quite catch that. {next_q}"
        else:
            msg = next_q

        return {
            'ai_speech': msg,
            'update_scribe': local_update,
            'is_complete': all(k in current_state for k in ['name', 'grade', 'board', 'interests', 'strengths'])
        }
        # End of CareerBrain class