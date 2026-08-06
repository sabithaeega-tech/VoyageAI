# VoyageAI

VoyageAI is an intelligent, multi-agent travel planning application built with Python, Streamlit, LangGraph, and Ollama. It helps users create personalized travel plans for any destination mentioned in the prompt, including itinerary generation, budget estimation, travel assistance, and reflection-based validation.

## Project Overview

VoyageAI combines multiple specialized agents to act like a travel concierge:
- Destination agent: identifies or builds a destination recommendation from the user prompt
- Itinerary agent: creates a day-by-day travel plan with morning, afternoon, evening, places to visit, and stay suggestions
- Budget agent: estimates travel costs for flights, accommodation, food, transport, activities, shopping, and contingency
- Travel assistance agent: provides visa guidance, weather notes, packing tips, local transport advice, and travel support information
- Reflection agent: evaluates whether the plan is complete, personalized, and budget-aware

The app is designed to work with user-provided destinations dynamically rather than being limited to a small predefined list.

## Reference Inspiration

The UI and conversational experience were inspired by the travel-planning style seen in:
- https://mindtrip.ai/chat/8831940

## Project Structure

- app.py: Streamlit web app entry point and user interface
- supervisor.py: parses the user request and coordinates the workflow
- graph.py: LangGraph workflow that connects the agents in sequence
- agents/: contains the specialized planning agents
  - destination_agent.py
  - itinerary_agent.py
  - budget_booking_agent.py
  - travel_assistance_agent.py
  - reflection_agent.py
- memory/: stores traveler state and conversation memory
- providers/: LLM provider integration, including Ollama support
- tools/: helper modules for destination search, visa lookup, currency conversion, budgeting, and weather
- tests/: regression tests for itinerary logic

## Features

- Dynamic destination planning from natural-language prompts
- Personalized itinerary generation for any destination mentioned by the user
- Budget-aware planning with suggested hotel, transport, activity, and food recommendations
- Travel support such as visa guidance, weather outlook, packing checklist, and local transport advice
- Traveler profile support including nationality, currency, travelers, duration, budget, season, transportation preference, accommodation preference, and interests
- Conversation memory for continuity across follow-up travel requests
- Modern Streamlit UI with chat-style presentation and trip overview cards

## Tech Stack

- Python 3.10+
- Streamlit
- LangGraph
- Ollama / LangChain-compatible provider support
- Pydantic
- pytest

## Installation

1. Clone the repository
2. Create a virtual environment (recommended)
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. If you are using Ollama locally, make sure the Ollama server is running and the model is available.

## Run the Application

```bash
streamlit run app.py
```

Once running, open the local Streamlit URL in your browser:
- http://localhost:8501

If you want to run it from the project folder directly, use:
- Project folder: C:\Users\dusnamoni.nandini\Desktop\CapStone\VoyageAI1.0

## Example Prompts

- Plan a 5-day trip to Kashmir under ₹50,000 for a couple with food and nature interests.
- Plan a 7-day honeymoon in Bali with a budget of ₹2,00,000.
- Suggest a solo backpacking trip to Vietnam under ₹80,000.
- Plan a 10-day Europe trip for a family of four in summer with culture and beach stops.

## Testing

Run the test suite with:

```bash
python -m pytest -q
```

## Notes

- The app can work even when the LLM backend is unavailable by falling back to structured local responses.
- The system is built to be extensible, so new agents or tools can be added without changing the overall structure.

## Future Improvements

- Add richer destination-specific recommendations using live travel APIs
- Improve itinerary personalization with more advanced memory and preference learning
- Add export to PDF/Word and calendar integration
- Enhance interactive chat follow-up refinement

## License

This project is intended for educational and demonstration purposes.


## Screen shots 
<img width="1913" height="930" alt="Screenshot 2026-08-06 130718" src="https://github.com/user-attachments/assets/7bec57db-64c5-4706-8c2b-335c775a9ae5" />


<img width="1899" height="934" alt="Screenshot 2026-08-06 130802" src="https://github.com/user-attachments/assets/f2babb36-9f0d-4b31-bfac-8c8adfe7c8bb" />


<img width="1849" height="831" alt="Screenshot 2026-08-06 130827" src="https://github.com/user-attachments/assets/401aaf50-e993-44d8-a5c8-6dd9fcbd0fa3" />

<img width="1900" height="890" alt="Screenshot 2026-08-06 130839" src="https://github.com/user-attachments/assets/7ec24b17-7bb3-4670-a6e6-da522212d636" />

<img width="1901" height="902" alt="Screenshot 2026-08-06 130848" src="https://github.com/user-attachments/assets/7fc82063-389c-4c47-8e35-e865133c1b5a" />

<img width="1896" height="910" alt="Screenshot 2026-08-06 130854" src="https://github.com/user-attachments/assets/2d84d257-8ec0-42ad-8147-36f3e2c53f7a" />




