"""
Class Tutor LangGraph – 5 Nodes Pipeline

Nodes:
1A – Structured Class Notes         -> GPT-4o
1B – Misconceptions                 -> GPT-4o-mini
2  – Practice & Challenges          -> GPT-4o
3  – Real-life & Resources (URLs)   -> GPT-5
4  – Actions & Feedback             -> GPT-4o-mini

Env:
  OPENAI_API_KEY  = your OpenAI key
  GEMINI_API_KEY  = (optional, not used yet but wired for later)

Run:
  python class_tutor_graph.py

You must have:
  pip install langgraph openai
"""

import os
from typing import TypedDict, Optional

from openai import OpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY in your environment.")

client = OpenAI(api_key=OPENAI_API_KEY)

# Model names (adjust to whatever your account exposes)
MODEL_NODE_1A = "gpt-4o"
MODEL_NODE_1B = "gpt-4o-mini"
MODEL_NODE_2 = "gpt-4o"
MODEL_NODE_3 = "gpt-5"      # you can change to your exact GPT-5 name if different
MODEL_NODE_4 = "gpt-4o-mini"


# ---------------------------------------------------------------------
# Shared helper to call OpenAI
# ---------------------------------------------------------------------


def call_openai(model: str, system_prompt: str, user_prompt: str) -> str:
    """Small helper to call OpenAI chat models and return text content."""
    base_payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    # Only add temperature if the model actually supports it
    if "gpt-5" not in model.lower():
        base_payload["temperature"] = 0.3

    resp = client.chat.completions.create(**base_payload)
    return resp.choices[0].message.content or ""


# ---------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------


class TutorState(TypedDict, total=False):
    # Input
    transcript: str
    student_level: str
    student_goal: str

    # Outputs per node
    notes_1a: str
    misconceptions_1b: str
    practice_2: str
    resources_3: str
    actions_4: str


# ---------------------------------------------------------------------
# Node 1A – Structured Class Notes (GPT-4o)
# ---------------------------------------------------------------------


def node_1a_notes(state: TutorState) -> TutorState:
    transcript = state["transcript"]
    level = state.get("student_level", "college")
    goal = state.get("student_goal", "exam preparation")

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

    user_prompt = f"""Student level: {level}
Student goal: {goal}

Transcript:
\"\"\"{transcript}\"\"\"

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

    notes = call_openai(MODEL_NODE_1A, system_prompt, user_prompt)
    return {**state, "notes_1a": notes}


# ---------------------------------------------------------------------
# Node 1B – Misconceptions (GPT-4o-mini)
# ---------------------------------------------------------------------


def node_1b_misconceptions(state: TutorState) -> TutorState:
    transcript = state["transcript"]
    notes = state.get("notes_1a", "")
    level = state.get("student_level", "college")

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

    user_prompt = f"""Student level: {level}

Transcript:
\"\"\"{transcript}\"\"\"

Output format:

# Likely Misconceptions

## Misconception 1: <short title>
- Why students might think this:
- Why this is wrong:
- Correct explanation (simple):

## Misconception 2: ...
"""

    misconceptions = call_openai(MODEL_NODE_1B, system_prompt, user_prompt)
    return {**state, "misconceptions_1b": misconceptions}

# ---------------------------------------------------------------------
# Node 2 – Practice & Challenges (GPT-4o)
# ---------------------------------------------------------------------


def node_2_practice(state: TutorState) -> TutorState:
    notes = state.get("notes_1a", "")
    misconceptions = state.get("misconceptions_1b", "")
    level = state.get("student_level", "college")
    goal = state.get("student_goal", "exam preparation")

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

    user_prompt = f"""Student level: {level}
Student goal: {goal}

Notes:
\"\"\"{notes}\"\"\"

Misconceptions:
\"\"\"{misconceptions}\"\"\"

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

    practice = call_openai(MODEL_NODE_2, system_prompt, user_prompt)
    return {**state, "practice_2": practice}


# ---------------------------------------------------------------------
# Node 3 – Real-life & Resources (GPT-5)
# ---------------------------------------------------------------------


def node_3_resources(state: TutorState) -> TutorState:
    notes = state.get("notes_1a", "")
    practice = state.get("practice_2", "")
    level = state.get("student_level", "college")
    goal = state.get("student_goal", "exam preparation")

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

    user_prompt = f"""Student level: {level}
Student goal: {goal}

Notes:
\"\"\"{notes}\"\"\"


Output format:

# Real-life Applications & Resources

## Concept 1: <name>
Short explanation (2–4 lines).

**Real-life applications**
- ...

**Resources**
- [Title] (Type: Article,YouTube shorts, Level: Beginner) – URL: ...
- [Title] (Type: YouTube, Level: Intermediate) – URL: ...
- [Title] (Type: Docs, Level: Advanced) – URL: ...

## Concept 2: ...
"""

    resources = call_openai(MODEL_NODE_3, system_prompt, user_prompt)
    return {**state, "resources_3": resources}


# ---------------------------------------------------------------------
# Node 4 – Actions & Feedback (GPT-4o-mini)
# ---------------------------------------------------------------------


def node_4_actions(state: TutorState) -> TutorState:
    notes = state.get("notes_1a", "")
    misconceptions = state.get("misconceptions_1b", "")
    practice = state.get("practice_2", "")
    resources = state.get("resources_3", "")
    level = state.get("student_level", "college")
    goal = state.get("student_goal", "exam preparation")

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

    user_prompt = f"""Student level: {level}
Student goal: {goal}

Notes:
\"\"\"{notes}\"\"\"

Misconceptions:
\"\"\"{misconceptions}\"\"\"



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

    actions = call_openai(MODEL_NODE_4, system_prompt, user_prompt)
    return {**state, "actions_4": actions}


# ---------------------------------------------------------------------
# Build LangGraph
# ---------------------------------------------------------------------


def build_tutor_graph():
    graph = StateGraph(TutorState)

    graph.add_node("node_1a_notes", node_1a_notes)
    graph.add_node("node_1b_misconceptions", node_1b_misconceptions)
    graph.add_node("node_2_practice", node_2_practice)
    graph.add_node("node_3_resources", node_3_resources)
    graph.add_node("node_4_actions", node_4_actions)

    graph.set_entry_point("node_1a_notes")
    graph.add_edge("node_1a_notes", "node_1b_misconceptions")
    graph.add_edge("node_1b_misconceptions", "node_2_practice")
    graph.add_edge("node_2_practice", "node_3_resources")
    graph.add_edge("node_3_resources", "node_4_actions")
    graph.add_edge("node_4_actions", END)

    return graph.compile()


# ---------------------------------------------------------------------
# Example main – plug your transcript here
# ---------------------------------------------------------------------

# ---------------------------------------------------------------------
# Helpers: combine node outputs + one-shot pipeline runner
# ---------------------------------------------------------------------

def combine_tutor_outputs(state: TutorState) -> tuple[str, dict]:
    """Return (combined_markdown, combined_json) from node outputs."""
    notes         = state.get("notes_1a", "").strip()
    misconceptions= state.get("misconceptions_1b", "").strip()
    practice      = state.get("practice_2", "").strip()
    resources     = state.get("resources_3", "").strip()
    actions       = state.get("actions_4", "").strip()

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


def run_tutor_pipeline(
    transcript: str,
    student_level: str = "college",
    student_goal: str = "exam preparation",
) -> dict:
    """
    Build and invoke the graph once, returning:
    {
      'final_state': <TutorState>,
      'combined_markdown': <str>,
      'combined_json': <dict>
    }
    """
    app = build_tutor_graph()
    init_state: TutorState = {
        "transcript": transcript,
        "student_level": student_level,
        "student_goal": student_goal,
    }
    final_state = app.invoke(init_state)
    combined_md, combined_json = combine_tutor_outputs(final_state)
    return {
        "final_state": final_state,
        "combined_markdown": combined_md,
        "combined_json": combined_json,
    }



