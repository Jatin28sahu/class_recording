r"""
Class Tutor LangGraph - Final Version (Provider & Model Parametrized)
Supports GPT-5, Gemini, Graph DAG dependencies, structured outputs.

Graph Flow:
    transcript
       |
  --------------------------
  |                        |
node_1a_notes      node_1b_misconception
  |         \            /            |
  |          \          /             |
  |           \        /              |
  |         (notes, misconceptions)   |
  |         /          |              |
  |        /           |              |
node_3_resources   node_2_practice   node_4_actions
    |                   |                   |
    -------- (All paths lead) ---------------
                       |
                      END
"""

# ---------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------
import os
from typing import TypedDict, Tuple, Dict, Any, Annotated
import operator
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

try:
    from langsmith import uuid7
except ImportError:
    # Fallback if langsmith is not installed or uuid7 is not available
    import uuid
    def uuid7():
        return str(uuid.uuid4())



load_dotenv()

# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not OPENAI_API_KEY and not GOOGLE_API_KEY:
    raise RuntimeError("You must set either OPENAI_API_KEY or GOOGLE_API_KEY.")

# ---------------------------------------------------------------------
# Node Model/Provider Configs
# ---------------------------------------------------------------------
MODEL_NODE_1A = ("gpt-4o", "openai")
MODEL_NODE_1B = ("gpt-4o-mini", "openai")
MODEL_NODE_2  = ("gpt-4o-mini", "openai")
MODEL_NODE_3  = ("gpt-5", "openai")
MODEL_NODE_4  = ("gemini-2.5-flash", "gemini")

# ---------------------------------------------------------------------
# LLM Helper using LangChain integrations for automatic token tracking
# ---------------------------------------------------------------------
def call_llm(provider: str, model: str, system_prompt: str, user_prompt: str) -> str:
    """
    Call LLM using LangChain integrations.
    
    LangChain automatically tracks token usage and sends it to LangSmith,
    eliminating the need for manual token extraction. Token counts, costs,
    and detailed breakdowns (cached tokens, reasoning tokens, etc.) are
    automatically captured and displayed in the LangSmith UI.
    """
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    if provider.lower() == "openai":
        # Configure temperature only for non-GPT-5 models
        if model.startswith("gpt-5"):
            llm = ChatOpenAI(model=model, api_key=OPENAI_API_KEY)
        else:
            llm = ChatOpenAI(model=model, temperature=0.3, api_key=OPENAI_API_KEY)
        
        # LangChain automatically tracks token usage in LangSmith
        response = llm.invoke(messages)
        return response.content.strip()
    
    elif provider.lower() == "gemini":
        # ChatGoogleGenerativeAI automatically tracks token usage
        llm = ChatGoogleGenerativeAI(model=model, google_api_key=GOOGLE_API_KEY,temperature=0.3)
        response = llm.invoke(messages)
        return response.content.strip()
    
    else:
        raise ValueError("provider must be 'openai' or 'gemini'")

# ---------------------------------------------------------------------
# State Definition with Annotated Types for Concurrent Updates
# ---------------------------------------------------------------------
class TutorState(TypedDict):
    # Input fields (single value)
    transcript: str
    student_level: str
    student_goal: str

    # Output fields (use Annotated with operator.add to handle multiple concurrent writes)
    # This prevents "Can receive only one value per step" error when nodes run in parallel
    notes_1a: Annotated[str, operator.add]
    misconceptions_1b: Annotated[str, operator.add]
    practice_2: Annotated[str, operator.add]
    resources_3: Annotated[str, operator.add]
    actions_4: Annotated[str, operator.add]

# ---------------------------------------------------------------------
# Node Functions
# ---------------------------------------------------------------------

def node_1a_notes(state: TutorState) -> TutorState:
    model, provider = MODEL_NODE_1A
    system_prompt = """You are Node 1A – Structured Class Notes Generator.
Your job is to convert a classroom transcript into clean, structured notes that a student can revise from.

Guidelines:
- Focus only on the content of this specific class session.
- Use clear, simple language suitable for the given student level.
- Be information-dense but not wordy.
- Do NOT invent topics that are not implied by the transcript.
- Use headings, bullet points, and clear formatting.
- Include:
  1) Short summary (1–3 short paragraphs)
  2) Section-wise notes with titles
  3) Small glossary (important terms + short definitions)
  4) Formula list (if there are formulas) with brief explanation
  5) Example index (brief description of examples discussed)
"""

    user_prompt = f"""
Student level: {state.get('student_level', 'college')}
Student goal: {state.get('student_goal', 'exam')}
Transcript:
\"\"\"{state['transcript']}\"\"\"

Produce the full detailed notes in this structure:

# Summary
- ...

# Section-wise Notes
## Section 1: ...
- ...

## Section 2: ...
- ...

# Glossary
- Term: short definition

# Formulas
- Formula: explanation

# Example Index
- Example: where it appears / what it shows
"""
    
    notes = call_llm(provider, model, system_prompt, user_prompt)
    return {"notes_1a": notes}


def node_1b_misconceptions(state: TutorState) -> dict:
    model, provider = MODEL_NODE_1B
    system_prompt = """You are Node 1B – Misconception Detector.
Your job is to look only at the class transcript and point out:
- likely misconceptions
- typical mistakes
- confusion points

You must:
- Use simple language suitable for the student level.
- For each misconception:
  - Name it
  - Explain why it is wrong
  - Give the correct explanation clearly
- Do NOT invent far-fetched misconceptions. Stay realistic.
"""


    user_prompt = f"""

Student level: {state.get('student_level', 'college')}
Student goal: {state.get('student_goal', 'exam')}
Transcript:
\"\"\"{state['transcript']}\"\"\"

Format:
## Misconception 1
- Why students think this:
- Why it’s wrong:
- Correct explanation:

## Misconception 2: ...
"""
    misconceptions = call_llm(provider, model, system_prompt, user_prompt)
    return {"misconceptions_1b": misconceptions}


def node_2_practice(state: TutorState) -> dict:
    model, provider = MODEL_NODE_2
    system_prompt = """You are Node 2 – Practice & Challenges Generator.
You design questions and solutions based on the notes and misconceptions.

Requirements:
- Focus on understanding, not rote.
- Include a mix of:
  - Concept-check MCQs
  - Short-answer questions
  - 1–2 deeper reasoning / proof / derivation questions (if relevant)
  - 1–2 application / word problems where possible
- For each question, also give a clear solution or marking scheme.
- Pay special attention to misconceptions and design questions to fix them.
"""


    user_prompt = f"""

Student level: {state.get('student_level', 'college')}
Student goal: {state.get('student_goal', 'exam')}
Notes:
\"\"\"{state.get('notes_1a', '')}\"\"\"
Misconceptions:
\"\"\"{state.get('misconceptions_1b', '')}\"\"\"

Output format:

# Practice Set

## Part A – Concept Check (MCQs)
Q1. ...
A. ...
B. ...
C. ...
D. ...
Correct answer: ...

(... a few more)

## Part B – Short Answer
Q1. ...
Suggested answer: ...

## Part C – Reasoning / Derivation
Q1. ...
Step-by-step solution:

## Part D – Application / Real-world Style
Q1. ...
Solution / reasoning:
"""
    practice = call_llm(provider, model, system_prompt, user_prompt)
    return {"practice_2": practice}


def node_3_resources(state: TutorState) -> dict:
    model, provider = MODEL_NODE_3
    system_prompt = """You are Node 3 – Real-life & Resources Generator.
Your job is to:
- Connect the class concepts to real-life applications.
- Suggest high-quality resources (articles, docs, YouTube videos).

Instructions:
1. Identify the main concepts from the notes.
2. For each main concept:
   - Give 1–2 real-life applications in simple language.
   - List 1–3 resources:
       - Direct URLs (articles/docs)
       - YouTube video links
3. Mark difficulty: Beginner / Intermediate / Advanced.
4. Prefer:
   - Short YouTube videos over any hour lectures which is relevent.
   - Trustworthy sources (official docs, well-known sites, reputable channels).
5. Do NOT invent concepts not in the notes.
"""
    user_prompt = f"""

Student level: {state.get('student_level', 'college')}
Student goal: {state.get('student_goal', 'exam')}
Notes:
\"\"\"{state.get('notes_1a', '')}\"\"\"

Output format:

# Real-life Applications & Resources

## Concept 1: <name>
Short explanation (2–4 lines).

**Real-life applications**
- ...

**Resources**
- [Title] (Type: Article,YouTube shorts and youtube short videos, Level: Beginner) – URL: ...
- [Title] (Type: YouTube, Level: Intermediate) – URL: ...
- [Title] (Type: Docs, Level: Advanced) – URL: ...

## Concept 2: ...
"""

    resources = call_llm(provider, model, system_prompt, user_prompt)
    return {"resources_3": resources}


def node_4_actions(state: TutorState) -> dict:
    model, provider = MODEL_NODE_4
    system_prompt = """You are Node 4 – Actions & Feedback Coach.
You take everything generated so far and turn it into:
- A short, realistic study plan
- Concrete next actions for the student
- Encouraging but honest feedback

Guidelines:
- Be specific and actionable.
- Use simple language.
- Keep it short enough to follow in real life.
- Base your advice on the notes, misconceptions.
"""
    user_prompt = f"""
Notes:
\"\"\"{state.get('notes_1a', '')}\"\"\"
Misconceptions:
\"\"\"{state.get('misconceptions_1b', '')}\"\"\"

Output format:

# Study Plan (Next 4 Days)
Day 1: ...
Day 2: ...
...

# How to Use the Notes & Practice
- ...

# Common Pitfalls to Avoid
- ...

# Motivational but Realistic Message
<3–6 lines>
"""
    actions = call_llm(provider, model, system_prompt, user_prompt)
    return {"actions_4": actions}

# ---------------------------------------------------------------------
# Combined Output Assembler
# ---------------------------------------------------------------------
def combine_tutor_outputs(state: TutorState) -> Tuple[str, Dict]:
    notes = state.get("notes_1a", "").strip()
    misconceptions = state.get("misconceptions_1b", "").strip()
    practice = state.get("practice_2", "").strip()
    resources = state.get("resources_3", "").strip()
    actions = state.get("actions_4", "").strip()

    combined_md = (
        "# Class Tutor – Combined Output\n\n"
        "## 1A – Structured Class Notes\n\n"
        f"{notes}\n\n"
        "## 1B – Likely Misconceptions\n\n"
        f"{misconceptions}\n\n"
        "## 2 – Practice & Challenges\n\n"
        f"{practice}\n\n"
        "## 3 – Real-life Applications & Resources\n\n"
        f"{resources}\n\n"
        "## 4 – Actions & Feedback\n\n"
        f"{actions}\n"
    )

    combined_json = {
        "notes_1a": notes,
        "misconceptions_1b": misconceptions,
        "practice_2": practice,
        "resources_3": resources,
        "actions_4": actions,
        "combined_text": combined_md,
    }
    return combined_md, combined_json

# ---------------------------------------------------------------------
# Build Graph
# ---------------------------------------------------------------------
def build_tutor_graph():
    graph = StateGraph(TutorState)

    graph.add_node("node_1a_notes", node_1a_notes)
    graph.add_node("node_1b_misconceptions", node_1b_misconceptions)
    graph.add_node("node_2_practice", node_2_practice)
    graph.add_node("node_3_resources", node_3_resources)
    graph.add_node("node_4_actions", node_4_actions)

    # Entry point
    graph.set_entry_point("node_1a_notes")

    # First branch
    graph.add_edge("node_1a_notes", "node_1b_misconceptions")

    # Downstream dependencies
    graph.add_edge("node_1a_notes", "node_3_resources")
    graph.add_edge("node_1b_misconceptions", "node_2_practice")
    graph.add_edge("node_1a_notes", "node_2_practice")
    graph.add_edge("node_1a_notes", "node_4_actions")
    graph.add_edge("node_1b_misconceptions", "node_4_actions")

    # Ending
    graph.add_edge("node_2_practice", END)
    graph.add_edge("node_3_resources", END)
    graph.add_edge("node_4_actions", END)

    return graph.compile()
# ---------------------------------------------------------------------
# One-shot Runner with LangSmith Tracing
# ---------------------------------------------------------------------
def run_tutor_pipeline(transcript: str, student_level="college", student_goal="exam"):
    """
    Run the complete tutor pipeline with LangSmith tracing enabled.
    
    LangSmith will automatically track:
    - All LLM API calls (OpenAI, Gemini)
    - Token usage per node
    - Execution time per node
    - Graph structure and flow
    - Input/output for each node
    
    View traces at: https://smith.langchain.com
    """
    app = build_tutor_graph()
    init_state = {
        "transcript": transcript,
        "student_level": student_level,
        "student_goal": student_goal,
    }
    
    # Configure LangSmith tracing with metadata
    # The LANGCHAIN_TRACING_V2 env var enables automatic tracing
    config = {
        "run_name": "Class Tutor Pipeline",
        "metadata": {
            "student_level": student_level,
            "student_goal": student_goal,
            "transcript_length": len(transcript),
            "models_used": {
                "node_1a": MODEL_NODE_1A[0],
                "node_1b": MODEL_NODE_1B[0],
                "node_2": MODEL_NODE_2[0],
                "node_3": MODEL_NODE_3[0],
                "node_4": MODEL_NODE_4[0],
            }
        },
        "tags": ["class-tutor", "parallel-graph", student_level, student_goal]
    }
    
    final_state = app.invoke(init_state, config=config)
    combined_md, combined_json = combine_tutor_outputs(final_state)
    
    return {
        "final_state": final_state,
        "combined_markdown": combined_md,
        "combined_json": combined_json,
    }

# ---------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------
if __name__ == "__main__":
    transcript = "Photosynthesis converts solar energy to chemical energy in plants..."
    result = run_tutor_pipeline(transcript)
    print(result["combined_markdown"])
