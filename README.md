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

Live demo (deployed): https://voyageai-dhjgtz5okqrng6wsfl9sjk.streamlit.app/

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

## Configuration & Environment Variables

Configure the app by setting the following environment variables (or export in your shell / CI environment):

- `OLLAMA_HOST` — URL to your Ollama server (default `http://localhost:11434`).
- `OLLAMA_MODEL` — model identifier to use (default `llama3.2:latest` or as configured by your Ollama instance).
- `OLLAMA_TEMPERATURE` — sampling temperature for LLM responses (default `0.2`).
- `STREAMLIT_SERVER_PORT` — optionally override the Streamlit port.

Examples (Windows PowerShell):

```powershell
$env:OLLAMA_HOST = 'http://localhost:11434'
$env:OLLAMA_MODEL = 'llama3.2:latest'
$env:OLLAMA_TEMPERATURE = '0.2'
streamlit run app.py
```

## Architecture & Data Flow

High level dataflow (user -> planning graph -> agents -> providers/tools -> UI):

```mermaid
flowchart LR
  User[User UI (Streamlit)] -->|prompt| App[app.py]
  App --> Supervisor[SupervisorAgent]
  Supervisor --> Graph[TravelPlannerGraph]
  Graph --> DA[Destination Agent]
  Graph --> IA[Itinerary Agent]
  Graph --> BA[Budget/Booking Agent]
  Graph --> TA[Travel Assistance Agent]
  Graph --> RA[Reflection Agent]
  IA --> Providers[Providers / Tools]
  BA --> Tools[Budget / Currency / Destination DB]
  Providers -->|LLM calls| Ollama[Ollama]
  Tools -->|local lookups| DestinationDB[tools.destination_search]
  Graph --> App
```

Each agent receives structured inputs (destination, interests, duration, budget, traveler profile) and returns structured outputs consumed by the next stage.

## Agents (detailed)

- `DestinationAgent`: identifies or builds a canonical destination object (name, region, tags, attractions, avg_daily_cost, visa info). Inputs: free-text hint, interests, budget, duration. Output: destination dict.
- `ItineraryAgent`: builds a JSON array of days (day, highlights, morning, afternoon, evening, places_to_visit, stay). It first tries the LLM provider and falls back to a local generator when unavailable.
- `BudgetBookingAgent`: estimates cost breakdowns and hotel suggestions using `tools/budget_calculator.py` and `tools/currency_converter.py`.
- `TravelAssistanceAgent`: collects visa guidance, weather forecasts, packing checklists, and local transport advice via `tools/` helpers and external APIs (when integrated).
- `ReflectionAgent`: performs a quick validation and confidence scoring on the assembled plan.

## Providers & Tools

- `providers/ollama_provider.py` adapts local Ollama or LangChain-compatible LLMs. If Ollama is unreachable, the provider returns a structured fallback string that the itinerary parser interprets conservatively.
- `tools/` contains small, pure-Python helpers that are easy to extend and test:
  - `destination_search.py` — local destination DB for quick matches; add entries here to improve local suggestions.
  - `visa_lookup.py` — simple visa rules mapping.
  - `currency_converter.py` — wrapper around exchange rates (stub or live API).
  - `budget_calculator.py` — simple budget estimator logic.
  - `weather_service.py` — basic weather lookup or stub for local testing.

## Deployment & Production Notes

- Run Ollama (or another LLM service) as a separate, secured service. Keep model hosts and credentials out of source control.
- Consider containerizing the app and Ollama model server for reproducible deployments. Add health checks and logging for production readiness.
- For high-volume use, add request throttling, caching for destination lookups, and rate-limited LLM call queuing.

## Troubleshooting

- LLM backend unavailable: The app will fall back to a local structured planner; install and run Ollama to get richer named attractions and narrative.
- Generic place names in itineraries: Add destination entries to `tools/destination_search.py` (name and `attractions`) so the itinerary agent can reference concrete POIs.
- Placeholder or invisible input text: If the UI shows low-contrast placeholders, update the CSS in `app.py` (we already apply a fix to make textarea background and placeholder readable).

## Contributing Checklist

- Open an issue describing the change or bug.
- Create a feature branch and include tests for new behavior when applicable.
- Keep changes focused and update `README.md` when adding new configuration or runtime behavior.

## Known Limitations

- Local destination DB is limited to a few examples — consider integrating a places API (Google Places, OpenTripMap) for broader coverage.
- The LLM prompt/response parsing expects valid JSON; malformed LLM output may be ignored by the parser and trigger fallbacks.
- No persistence layer: conversation memory is ephemeral (session-based). Add a database if you need cross-session user history.

---


## Screen shots 
<img width="1913" height="930" alt="Screenshot 2026-08-06 130718" src="https://github.com/user-attachments/assets/7bec57db-64c5-4706-8c2b-335c775a9ae5" />


<img width="1899" height="934" alt="Screenshot 2026-08-06 130802" src="https://github.com/user-attachments/assets/f2babb36-9f0d-4b31-bfac-8c8adfe7c8bb" />


<img width="1849" height="831" alt="Screenshot 2026-08-06 130827" src="https://github.com/user-attachments/assets/401aaf50-e993-44d8-a5c8-6dd9fcbd0fa3" />

<img width="1900" height="890" alt="Screenshot 2026-08-06 130839" src="https://github.com/user-attachments/assets/7ec24b17-7bb3-4670-a6e6-da522212d636" />

<img width="1901" height="902" alt="Screenshot 2026-08-06 130848" src="https://github.com/user-attachments/assets/7fc82063-389c-4c47-8e35-e865133c1b5a" />

<img width="1896" height="910" alt="Screenshot 2026-08-06 130854" src="https://github.com/user-attachments/assets/2d84d257-8ec0-42ad-8147-36f3e2c53f7a" />




