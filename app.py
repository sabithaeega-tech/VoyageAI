import warnings

try:
    from langchain_core._api.deprecation import LangChainPendingDeprecationWarning
    warnings.filterwarnings('ignore', category=LangChainPendingDeprecationWarning)
except ImportError:
    pass

import streamlit as st
from supervisor import SupervisorAgent

st.set_page_config(page_title='VoyageAI Travel Planner', layout='wide')
supervisor = SupervisorAgent()

st.title('VoyageAI')
st.subheader('Intelligent Multi-Agent Travel Planning & Assistance Platform')

with st.sidebar:
    st.header('Traveler Profile')
    nationality = st.selectbox('Nationality', ['Indian', 'American', 'British', 'Australian', 'Other'])
    currency = st.selectbox('Currency', ['INR', 'USD', 'EUR', 'GBP', 'JPY'])
    travelers = st.number_input('Travelers', min_value=1, max_value=10, value=1)
    duration = st.number_input('Days', min_value=1, max_value=30, value=5)
    budget = st.number_input('Budget', min_value=0.0, value=150000.0, step=500.0)
    travel_dates = st.text_input('Travel dates (YYYY-MM-DD)', '')

st.markdown(
    'Use the field below to describe your travel plan, including destination, duration, budget, travelers, dates, and interests. Example: Plan a 7-day family trip to Japan in November with a budget of 200000 INR.'
)
user_input = st.text_area('Travel request', height=160)

if st.button('Generate Travel Plan'):
    if not user_input.strip():
        st.error('Please enter a travel request.')
    else:
        user_profile = {
            'nationality': nationality,
            'currency': currency,
            'travelers': travelers,
            'duration': duration,
            'budget': budget,
            'travel_dates': travel_dates or None,
        }

        result = supervisor.handle_request(user_input, user_profile)

        st.success('Travel plan generated successfully.')

        st.subheader('📍 Destination Recommendation')
        for item in result['destination_recommendations'][:3]:
            st.markdown(f"### {item['name']} ⭐ Recommended")
            st.markdown(f"**Reason:** {item.get('reason', 'Recommended based on your request.')}\n\n")
            st.markdown(f"**Weather:** {item.get('weather')}\n\n**Best Months:** {item.get('best_months')}\n\n**Visa:** {item.get('visa')}")
            st.markdown(f"**Tags:** {', '.join(item.get('tags', []))}")
            st.markdown(f"**Top attractions:** {', '.join(item.get('attractions', [])[:4])}")
            st.write('---')

        st.subheader('🗓 Itinerary')
        for stop in result.get('itinerary', []):
            day_label = stop.get('day', 'Day')
            st.markdown(f"**{day_label}**")
            for activity in stop.get('highlights', []):
                st.markdown(f"- {activity}")
            st.write('---')

        st.subheader('💰 Budget Estimate')
        budget_data = result.get('budget', {})
        total_cost = budget_data.get('total', 'N/A')
        budget_currency = budget_data.get('currency', currency)
        st.markdown(f"**Total estimated cost:** {total_cost} {budget_currency}")
        st.markdown(f"**Budget requested:** {budget_data.get('budget_requested', budget)} {budget_currency}")
        st.markdown(f"**Remaining / overrun:** {budget_data.get('budget_difference', 'N/A')} {budget_currency}")
        st.markdown('**Breakdown:**')
        breakdown = budget_data.get('breakdown', {})
        st.write(f"Accommodation: {breakdown.get('accommodation', 'N/A')} {budget_currency}")
        st.write(f"Flights: {breakdown.get('flights', 'N/A')} {budget_currency}")
        st.write(f"Food: {breakdown.get('food', 'N/A')} {budget_currency}")
        st.write(f"Transport: {breakdown.get('transport', 'N/A')} {budget_currency}")
        st.write(f"Activities: {breakdown.get('activities', 'N/A')} {budget_currency}")
        st.write(f"Shopping: {breakdown.get('shopping', 'N/A')} {budget_currency}")
        st.write(f"Contingency: {breakdown.get('contingency', 'N/A')} {budget_currency}")
        if budget_data.get('budget_friendly_advice'):
            st.info(budget_data['budget_friendly_advice'])

        st.subheader('🛂 Travel Assistance')
        assistance = result['travel_assistance']
        st.write(f"**Visa guidance:** {assistance['visa_guidance']}")
        st.write(f"**Notes:** {assistance['visa_notes']}")
        st.write(f"**Weather forecast:** {assistance['weather_forecast']}")
        st.write(f"**Emergency:** {assistance['emergency_numbers']}")
        st.write(f"**Currency:** {assistance['currency']}")
        st.write(f"**Language:** {assistance['language']}")
        st.write(f"**Time Zone:** {assistance['time_zone']}")
        st.write(f"**Power Plug:** {assistance['power_plug']}")
        st.write(f"**Local Transportation:** {assistance['local_transport']}")
        st.write(f"**Safety Tips:** {assistance['safety_tips']}")
        if assistance.get('packing_tips'):
            st.write(f"**Packing tips:** {assistance['packing_tips']}")

        st.subheader('✅ Reflection Report')
        st.write(result['reflection']['summary'])
        st.write(f"Confidence score: {result['reflection'].get('confidence_score', 'N/A')}")
        st.write(result['reflection']['validation'])

        st.download_button(
            label='Download itinerary summary',
            data='\n'.join([
                f"{stop['day']}: {', '.join(stop['highlights'])}" for stop in result['itinerary']
            ]),
            file_name='itinerary.txt',
            mime='text/plain',
        )
