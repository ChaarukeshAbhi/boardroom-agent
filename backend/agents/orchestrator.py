# backend/agents/orchestrator.py

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from agents.observer import ObserverAgent
from agents.archivist import ArchivistAgent


# -------------------- STATE --------------------
class MeetingState(TypedDict):
    audio_path: str
    title: str

    transcript: Optional[str]
    language: Optional[str]

    summary: Optional[str]
    meeting_id: Optional[str]


# -------------------- NODES --------------------

def observer_node(state: MeetingState) -> MeetingState:
    """
    LangGraph node:
    - Runs ObserverAgent
    - Adds transcript + language to state
    """
    observer = ObserverAgent()

    result = observer.run(state["audio_path"])

    return {
        **state,
        "transcript": result["transcript"],
        "language": result["language"],
    }


def archivist_node(state: MeetingState) -> MeetingState:
    """
    LangGraph node:
    - Runs ArchivistAgent
    - Generates summary
    - Stores meeting in Supabase
    """
    archivist = ArchivistAgent()

    summary_data = archivist.generate_summary(
        state["transcript"],
        state["language"]
    )

    meeting_id = archivist.store_meeting({
        "title": state["title"],
        "transcript": state["transcript"],
        "language": state["language"],
        "summary": summary_data["summary"],
    })

    return {
        **state,
        "summary": summary_data["summary"],
        "meeting_id": meeting_id,
    }


# -------------------- LANGGRAPH --------------------

graph = StateGraph(MeetingState)

graph.add_node("observer", observer_node)
graph.add_node("archivist", archivist_node)

graph.set_entry_point("observer")
graph.add_edge("observer", "archivist")
graph.add_edge("archivist", END)

meeting_graph = graph.compile()

# expose orchestrator for backward compatibility
orchestrator = graph
# -------------------- PUBLIC API --------------------

async def process_meeting(audio_path: str, title: str) -> MeetingState:
    """
    Entry point used by:
    - Recall webhook
    - Backend routes
    """
    initial_state: MeetingState = {
        "audio_path": audio_path,
        "title": title,
        "transcript": None,
        "language": None,
        "summary": None,
        "meeting_id": None,
    }

    final_state = meeting_graph.invoke(initial_state)
    return final_state
