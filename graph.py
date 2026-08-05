import warnings
from typing import Any, Dict, List, TypedDict

try:
    from langchain_core._api.deprecation import LangChainPendingDeprecationWarning
    warnings.filterwarnings('ignore', category=LangChainPendingDeprecationWarning)
except ImportError:
    pass

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime

from agents.budget_booking_agent import BudgetBookingAgent
from agents.destination_agent import DestinationRecommendationAgent
from agents.itinerary_agent import ItineraryPlannerAgent
from agents.reflection_agent import ReflectionAgent
from agents.travel_assistance_agent import TravelAssistanceAgent
from memory.conversation_memory import ConversationMemory


class TravelPlannerGraph:
    class State(TypedDict, total=False):
        request_data: Dict[str, Any]
        destination: List[Dict[str, Any]]
        itinerary: List[Dict[str, Any]]
        budget: Dict[str, Any]
        travel_assistance: Dict[str, Any]
        reflection: Dict[str, Any]

    class Context(TypedDict, total=False):
        memory: ConversationMemory

    def __init__(self) -> None:
        self.destination_agent = DestinationRecommendationAgent()
        self.itinerary_agent = ItineraryPlannerAgent()
        self.budget_agent = BudgetBookingAgent()
        self.assistance_agent = TravelAssistanceAgent()
        self.reflection_agent = ReflectionAgent()

        self.graph = StateGraph(state_schema=self.State, context_schema=self.Context)
        self.graph.add_node('destination', self.run_destination)
        self.graph.add_node('itinerary', self.run_itinerary)
        self.graph.add_node('budget', self.run_budget)
        self.graph.add_node('travel_assistance', self.run_assistance)
        self.graph.add_node('reflection', self.run_reflection)

        self.graph.add_edge(START, 'destination')
        self.graph.add_edge('destination', 'itinerary')
        self.graph.add_edge('itinerary', 'budget')
        self.graph.add_edge('budget', 'travel_assistance')
        self.graph.add_edge('travel_assistance', 'reflection')
        self.graph.add_edge('reflection', END)

        self.compiled_graph = self.graph.compile()

    def run(self, request_data: Dict[str, Any], memory: ConversationMemory) -> Dict[str, Any]:
        state = {'request_data': request_data}
        context = {'memory': memory}
        output = self.compiled_graph.invoke(state, context=context)

        return {
            'destination_recommendations': output.get('destination', []),
            'itinerary': output.get('itinerary', []),
            'budget': output.get('budget', {}),
            'travel_assistance': output.get('travel_assistance', {}),
            'reflection': output.get('reflection', {}),
        }

    def run_destination(self, state: State, runtime: Runtime[Context]) -> State:
        request = state['request_data']
        recommendations = self.destination_agent.recommend(
            interests=request.get('interests', []),
            budget=request.get('budget', 0),
            duration=request.get('duration', 5),
            preferred_region=request.get('preferred_region', ''),
            destination_hint=request.get('destination_hint') or request.get('last_destination'),
        )
        return {'destination': recommendations}

    def run_itinerary(self, state: State, runtime: Runtime[Context]) -> State:
        request = state['request_data']
        destination_list = state.get('destination', []) or []
        primary = destination_list[0] if destination_list else {'name': 'A popular destination', 'tags': []}
        itinerary = self.itinerary_agent.generate(
            destination=primary,
            duration=request.get('duration', 5),
            interests=request.get('interests', []),
            budget=request.get('budget', 0),
            currency=request.get('currency', 'USD'),
            travel_dates=request.get('travel_dates'),
        )
        return {'itinerary': itinerary}

    def run_budget(self, state: State, runtime: Runtime[Context]) -> State:
        request = state['request_data']
        primary = (state.get('destination') or [{'name': 'A popular destination', 'currency': 'USD', 'avg_daily_cost': 150}])[0]
        budget_data = self.budget_agent.estimate(
            destination=primary,
            duration=request.get('duration', 5),
            travelers=request.get('travelers', 1),
            budget=request.get('budget', 0),
            currency=request.get('currency', 'INR'),
            accommodation_style=request.get('accommodation_style', 'moderate'),
            nationality=request.get('nationality'),
        )
        return {'budget': budget_data}

    def run_assistance(self, state: State, runtime: Runtime[Context]) -> State:
        request = state['request_data']
        destination_list = state.get('destination', []) or []
        primary = destination_list[0] if destination_list else {'name': 'A popular destination'}
        assistance_data = self.assistance_agent.provide(
            destination=primary['name'],
            travel_dates=request.get('travel_dates'),
            nationality=request.get('nationality'),
        )
        return {'travel_assistance': assistance_data}

    def run_reflection(self, state: State, runtime: Runtime[Context]) -> State:
        request = state['request_data']
        budget = state.get('budget', {})
        itinerary = state.get('itinerary', [])
        destination_list = state.get('destination', []) or []
        destination = destination_list[0] if destination_list else {'name': 'Unknown destination', 'region': ''}
        assistance = state.get('travel_assistance', {})
        memory = runtime.context.get('memory') if runtime.context else None
        memory_notes = memory.get_context() if memory else ''

        reflection = self.reflection_agent.analyze(
            request=request,
            destination=destination,
            itinerary=itinerary,
            budget=budget,
            assistance=assistance,
            memory_context=memory_notes,
        )

        return {'reflection': reflection}

    def _calculate_confidence(self, budget: Dict[str, Any], itinerary: List[Dict[str, str]], request: Dict[str, Any], destination: Dict[str, Any]) -> int:
        score = 50
        if budget.get('budget_difference') is not None:
            if budget['budget_difference'] >= 0:
                score += 20
            else:
                score -= 10
        if len(itinerary) >= request.get('duration', 1):
            score += 10
        if destination.get('region') and request.get('preferred_region') and request['preferred_region'].lower() in destination['region'].lower():
            score += 5
        if request.get('travel_dates'):
            score += 5
        if request.get('interests'):
            score += 5
        return min(max(score, 0), 100)


def assistance_data_summary(budget: Dict[str, Any], request: Dict[str, Any]) -> str:
    budget_value = budget.get('total_converted', budget.get('total', 0))
    currency = budget.get('currency', request.get('currency', 'INR'))
    return f"Estimated total {budget_value} {currency}, travel dates {request.get('travel_dates', 'Flexible')}" if budget_value else 'No budget data available.'
