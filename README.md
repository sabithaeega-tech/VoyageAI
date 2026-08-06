# VoyageAI

VoyageAI is an intelligent, multi-agent travel-planning assistant built with Python and Streamlit. It combines lightweight local tools and an LLM provider (Ollama by default) to generate personalized itineraries, estimate budgets, and provide travel assistance (visa, weather, packing, transport) from a single conversational prompt.

This README explains how the project is organized, how the main components work together, and how to run and extend the system locally.

**Highlights:**
- Natural-language prompts produce a day-by-day itinerary, places-to-visit, and stay recommendations.
- Multi-agent architecture (destination, itinerary, budget, travel assistance, reflection) for modular and extensible planning.
- Local fallbacks and helper tools allow the app to function even if the LLM backend is unavailable.

---

## Quick Start

- Create and activate a Python virtual environment (recommended):

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

- Install dependencies:

```bash
pip install -r requirements.txt
```

- (Optional) Start Ollama if you plan to use the LLM provider locally and configure the `OLLAMA_HOST` / `OLLAMA_MODEL` env vars.

- Run the Streamlit app:

```bash
streamlit run app.py
```

Open the provided local URL (usually http://localhost:8501) and try one of the sample prompts.

---

## Repository Layout

- `app.py` — Streamlit frontend. Handles UI, user profile inputs, sample prompts, and displays the generated itinerary, budget, and travel support sections.
- `supervisor.py` — Top-level coordinator: parses user prompt, extracts structured request fields, updates conversation memory, and runs the workflow graph.
- `graph.py` — Workflow orchestration (LangGraph) wiring the agents and data flow for a complete travel plan.
- `agents/` — Specialized agents that perform discrete tasks:
  - `destination_agent.py` — Chooses or builds a destination record and metadata.
  - `itinerary_agent.py` — Generates day-by-day itinerary JSON (via LLM or local fallback) and extracts place names & stay suggestions.
  - `budget_booking_agent.py` — Estimates and breaks down trip costs.
  - `travel_assistance_agent.py` — Gathers visa, weather, packing, and local transport information.
  - `reflection_agent.py` — Validates plan completeness and generates a confidence score/summary.
- `providers/` — LLM provider adapters (Ollama integration) and safe fallbacks.
- `tools/` — Small, testable utility modules (destination search DB, visa lookup, currency conversion, budget estimator, weather stub).
- `memory/` — Conversation and traveler state persistence (in-memory/session-state by default).
- `tests/` — Unit tests (pytest) for core logic such as itinerary parsing and budgeting.

---

## How It Works (high level)

1. User enters a natural-language prompt and sets a traveler profile in the Streamlit UI.
2. `supervisor.py` parses structured fields (duration, budget, interests, destination hint) and updates `ConversationMemory`.
3. The `TravelPlannerGraph` executes the agents in order, passing structured data between them.
4. The `ItineraryAgent` attempts to call the LLM (via `providers/ollama_provider.py`) with a structured prompt that requests JSON. If the provider is unavailable, a local fallback generates a structured but simpler itinerary.
5. The results (itinerary, budget breakdown, travel assistance, reflection summary) are returned to the UI and stored in memory for follow-ups.

Key design goals: modular agents, clear JSON contract for itinerary output, graceful fallbacks, and an easy-to-extend local tools layer.

---

## Important Files & Where to Look

- `agents/itinerary_agent.py` — logic for building prompts, parsing LLM JSON responses, extracting place names and stay suggestions. If you see generic phrases like "visit a top-rated attraction", it likely means the destination record had no `attractions` populated.
- `tools/destination_search.py` — small local DB used for quick destination matching. Add entries here to improve local recommendations (for example add "Kashmir" with known attractions and hotels).
- `providers/ollama_provider.py` — LLM integration and local tool-call adapters. Configure `OLLAMA_HOST`, `OLLAMA_MODEL`, and `OLLAMA_TEMPERATURE` via environment variables.
- `supervisor.py` — parsing helpers are here (destination, budget, dates, interests). Tweak extraction regexes to improve detection from prompts.

---

## Extending Destinations (practical)

To include a new destination (for example, Kashmir) with named attractions and better stay suggestions:

1. Edit `tools/destination_search.py` and add an entry to the `DESTINATIONS` list. Include: `name`, `region`, `tags`, `avg_daily_cost`, `visa_required`, `currency`, and an `attractions` list.
2. The `DestinationRecommendationAgent` will attempt to match hint text to records in `DESTINATIONS` and return the enriched record to the itinerary agent.

This quick data-driven approach provides immediate improvements without calling external APIs.

---

## Running Tests

Run unit tests with `pytest`:

```bash
python -m pytest -q
```

Tests focus on itinerary parsing, tools behavior, and basic provider fallbacks.

---

## Development Notes

- The app stores short-term conversation state in `memory/conversation_memory.py` and in `st.session_state` during UI sessions.
- If you change prompt templates in `agents/itinerary_agent.py`, update parsing logic in the same file — the code expects the LLM to return a JSON array describing each day.
- To test LLM-driven behavior without a local Ollama server, either install Ollama or mock `providers.OllamaProvider.generate` in tests.

---

## Contribution & License

- Contributions welcome: open an issue or a PR for bug fixes, destination additions, or new agents.
- This repository is intended for educational and demonstration purposes. If you plan to use it in production, please add an appropriate open-source license and review third-party models and data sources.

---


## Screen shots 
<img width="1913" height="930" alt="Screenshot 2026-08-06 130718" src="https://github.com/user-attachments/assets/7bec57db-64c5-4706-8c2b-335c775a9ae5" />


<img width="1899" height="934" alt="Screenshot 2026-08-06 130802" src="https://github.com/user-attachments/assets/f2babb36-9f0d-4b31-bfac-8c8adfe7c8bb" />


<img width="1849" height="831" alt="Screenshot 2026-08-06 130827" src="https://github.com/user-attachments/assets/401aaf50-e993-44d8-a5c8-6dd9fcbd0fa3" />

<img width="1900" height="890" alt="Screenshot 2026-08-06 130839" src="https://github.com/user-attachments/assets/7ec24b17-7bb3-4670-a6e6-da522212d636" />

<img width="1901" height="902" alt="Screenshot 2026-08-06 130848" src="https://github.com/user-attachments/assets/7fc82063-389c-4c47-8e35-e865133c1b5a" />

<img width="1896" height="910" alt="Screenshot 2026-08-06 130854" src="https://github.com/user-attachments/assets/2d84d257-8ec0-42ad-8147-36f3e2c53f7a" />




