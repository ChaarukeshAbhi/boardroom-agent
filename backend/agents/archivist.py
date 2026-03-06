# agents/archivist.py

import os
from supabase import create_client
import google.generativeai as genai
from utils.config import settings
from typing import List, Dict

# ==============================
# Environment Variables
# ==============================

SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY
GEMINI_API_KEY = settings.GEMINI_API_KEY

# ==============================
# Initialize Clients
# ==============================

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# ==============================
# Archivist Agent
# ==============================

class ArchivistAgent:

    def __init__(self):
        self.table_name = "transcripts"

    # ==========================================
    # STORE TRANSCRIPT (One row per segment)
    # ==========================================
    def store_transcript(self, meeting_id: str, transcript: List[Dict]):

        rows = []

        for segment in transcript:
            row = {
                "meeting_id": meeting_id,
                "speaker": segment.get("speaker"),
                "text": segment.get("text"),
                "timestamp": segment.get("timestamp"),
                "confidence": segment.get("confidence"),
                "language": segment.get("language")
            }

            rows.append(row)

        supabase.table(self.table_name).insert(rows).execute()

        return {"status": "stored", "segments": len(rows)}

    # ==========================================
    # GET MEETING TRANSCRIPT
    # ==========================================
    def get_meeting_transcript(self, meeting_id: str):

        response = supabase.table(self.table_name)\
            .select("*")\
            .eq("meeting_id", meeting_id)\
            .order("timestamp")\
            .execute()

        return response.data

    # ==========================================
    # GET MEETING HISTORY
    # ==========================================
    def get_meeting_history(self):

        response = supabase.table(self.table_name)\
            .select("meeting_id")\
            .execute()

        meetings = list(set([row["meeting_id"] for row in response.data]))

        return meetings

    # ==========================================
    # BUILD CONTEXT FOR RAG
    # ==========================================
    def build_context(self, segments):

        context = ""

        for s in segments:
            speaker = s["speaker"]
            text = s["text"]

            context += f"{speaker}: {text}\n"

        return context

    # ==========================================
    # GENERATE SUMMARY (RAG)
    # ==========================================
    def generate_summary(self, meeting_id: str):

        segments = self.get_meeting_transcript(meeting_id)

        if not segments:
            return {"summary": "No transcript found."}

        context = self.build_context(segments)

        prompt = f"""
        You are a meeting intelligence assistant.

        Summarize the following meeting transcript clearly.

        Transcript:
        {context}

        Provide:
        - Key discussion points
        - Important decisions
        - Action items
        """

        response = model.generate_content(prompt)

        return {
            "meeting_id": meeting_id,
            "summary": response.text
        }

    # ==========================================
    # ASK AI ABOUT MEETING
    # ==========================================
    def ask_meeting(self, meeting_id: str, question: str):

        segments = self.get_meeting_transcript(meeting_id)

        context = self.build_context(segments)

        prompt = f"""
        Answer the question using the meeting transcript.

        Transcript:
        {context}

        Question:
        {question}
        """

        response = model.generate_content(prompt)

        return {"answer": response.text}

    # ==========================================
    # COMPARE TWO MEETINGS
    # ==========================================
    def compare_meetings(self, meeting1: str, meeting2: str):

        seg1 = self.get_meeting_transcript(meeting1)
        seg2 = self.get_meeting_transcript(meeting2)

        context1 = self.build_context(seg1)
        context2 = self.build_context(seg2)

        prompt = f"""
        Compare the following two meetings.

        Meeting 1:
        {context1}

        Meeting 2:
        {context2}

        Provide:
        - Differences
        - Similar discussion topics
        - New decisions in Meeting 2
        """

        response = model.generate_content(prompt)

        return {
            "meeting1": meeting1,
            "meeting2": meeting2,
            "comparison": response.text
        }