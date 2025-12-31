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
        if not s.get('values'):
            return "What are some core values that matter to you? (e.g., helping others, innovation, stability, adventure?)"
        if not s.get('work_environment'):
            return "What kind of work environment do you prefer? (e.g., office, outdoors, remote, team-based?)"
        if not s.get('goals'):
            return "What are your long-term goals or dreams? (e.g., making a difference, building something new, traveling?)"
        
        return "I've gathered some great insights! Would you like to see your personalized career discovery report?"

    @st.cache_data
    def cached_llm_extract(_self, user_input):
        """Uses LLM to generically extract interests/strengths/values with caching to save memory."""
        prompt = f"""
        Analyze the user input and extract:
        1. Interests (hobbies/subjects)
        2. Strengths (skills/traits)
        3. Values (core principles like helping others, innovation)
        4. Work Environment (preferred setting like office, outdoors)
        5. Goals (long-term aspirations)
        Return ONLY a JSON object: {{"interests": [], "strengths": [], "values": [], "work_environment": "", "goals": ""}}. 
        If none found, return empty lists/strings.
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
            return {"interests": [], "strengths": [], "values": [], "work_environment": "", "goals": ""}

    @st.cache_data
    def generate_career_paths(_self, scribe_data):
        """Generate career recommendations based on scribe data."""
        prompt = f"""
        Based on the following student profile, suggest 3-5 suitable career paths. Explain briefly why each fits.
        Profile:
        - Name: {scribe_data['name']}
        - Grade: {scribe_data['grade']}
        - Board: {scribe_data['board']}
        - Interests: {', '.join(scribe_data['interests'])}
        - Strengths: {', '.join(scribe_data['strengths'])}
        - Values: {', '.join(scribe_data['values'])}
        - Work Environment: {scribe_data['work_environment']}
        - Goals: {scribe_data['goals']}
        
        Return ONLY a JSON object: {{"paths": [{{"path": "Career Name", "reason": "Brief explanation"}}]}}
        """
        try:
            chat_completion = _self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a career advisor. Output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model=_self.model,
                response_format={"type": "json_object"}
            )
            result = json.loads(chat_completion.choices[0].message.content)
            return [item['path'] for item in result.get('paths', [])]
        except Exception:
            return []

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

        # 2. LLM for Unstructured data (Interests, Strengths, Values, etc.)
        if scribe_data.get('board') and any(not scribe_data.get(k) for k in ['interests', 'strengths', 'values', 'work_environment', 'goals']):
            extracted = self.cached_llm_extract(ui_raw)
            for key in ['interests', 'strengths', 'values']:
                if extracted.get(key):
                    local_update[key] = list(set(scribe_data.get(key, []) + extracted[key]))
            for key in ['work_environment', 'goals']:
                if extracted.get(key):
                    local_update[key] = extracted[key]

        # 3. Final State Sync
        current_state = {**scribe_data, **local_update}
        
        # Generate paths if complete and not already generated
        if all(k in current_state and current_state[k] for k in ['name', 'grade', 'board', 'interests', 'strengths', 'values', 'work_environment', 'goals']) and not current_state.get('paths'):
            paths = self.generate_career_paths(current_state)
            local_update['paths'] = paths
        
        next_q = self._get_next_question(current_state)

        # Prevent repeating the same question if no new info was found
        if not local_update and user_input:
            msg = f"I didn't quite catch that. {next_q}"
        else:
            msg = next_q

        return {
            'ai_speech': msg,
            'update_scribe': local_update,
            'is_complete': bool(current_state.get('paths'))
        }
        # End of CareerBrain class