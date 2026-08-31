"""LangGraph workflow assembly and compilation."""

from langgraph.graph import END, START, StateGraph
from app.graph.nodes.discovery import discover_and_score_jobs_node
from app.graph.nodes.github_match import match_github_projects_node
from app.graph.nodes.prep import generate_interview_prep_node
from app.graph.nodes.resume import tailor_resume_node
from app.graph.state import JobSearchState


def create_job_search_graph():
    """Create and compile the stateful LangGraph agent graph."""
    workflow = StateGraph(JobSearchState)

    # Register Nodes
    workflow.add_node("discover_jobs", discover_and_score_jobs_node)
    workflow.add_node("match_projects", match_github_projects_node)
    workflow.add_node("tailor_resume", tailor_resume_node)
    workflow.add_node("prepare_interview", generate_interview_prep_node)

    # Define Control Flow & Edges
    workflow.add_edge(START, "discover_jobs")
    workflow.add_edge("discover_jobs", "match_projects")
    workflow.add_edge("match_projects", "tailor_resume")
    workflow.add_edge("tailor_resume", "prepare_interview")
    workflow.add_edge("prepare_interview", END)

    return workflow.compile()


# Pre-compiled graph instance
job_search_graph = create_job_search_graph()
