import warnings

try:
    from langchain_core._api.deprecation import LangChainPendingDeprecationWarning
    warnings.filterwarnings('ignore', category=LangChainPendingDeprecationWarning)
except ImportError:
    pass

import streamlit as st
from supervisor import SupervisorAgent

st.set_page_config(page_title='VoyageAI Travel Planner', layout='wide')

if 'supervisor' not in st.session_state:
    st.session_state.supervisor = SupervisorAgent()
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'latest_result' not in st.session_state:
    st.session_state.latest_result = None

st.markdown(
    """
    <style>
    .stApp {
        background: var(--background-color);
        color: var(--text-color);
    }
    [data-testid="stSidebar"] {
        background: var(--secondary-background-color);
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input,
    .stMultiSelect > div > div > div {
        background: var(--background-color);
        color: var(--text-color);
        border: 1px solid var(--border-color);
        border-radius: 10px;
    }
    .stButton > button {
        background: linear-gradient(90deg, #2563eb, #38bdf8);
        color: white;
        border: none;
        border-radius: 999px;
    }
    .stExpander {
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 0.35rem 0.6rem;
        margin-bottom: 0.6rem;
    }
    .stMarkdownContainer, .stTextInput, .stTextArea, .stSelectbox, .stNumberInput, .stMultiSelect {
        color: var(--text-color);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_bubble(role: str, text: str) -> None:
    if role == 'user':
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg, #2563eb, #38bdf8); color:white; padding:14px 16px; border-radius:18px 18px 4px 18px; margin:8px 0; max-width:80%; margin-left:auto; box-shadow:0 8px 20px rgba(37, 99, 235, 0.16);">
                {text}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background:var(--secondary-background-color); color:var(--text-color); padding:14px 16px; border-radius:18px 18px 18px 4px; margin:8px 0; max-width:90%; border:1px solid var(--border-color); box-shadow:0 4px 12px rgba(15, 23, 42, 0.06);">
                {text}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_card(title: str, value: str, caption: str) -> None:
    st.markdown(
        f"""
        <div style="background:var(--secondary-background-color); border:1px solid var(--border-color); border-radius:16px; padding:14px; margin:6px 0; box-shadow:0 8px 24px rgba(15, 23, 42, 0.06);">
            <div style="font-size:0.8rem; color:#2563eb; font-weight:600;">{title}</div>
            <div style="font-size:1.2rem; font-weight:700; margin-top:4px; color:var(--text-color);">{value}</div>
            <div style="font-size:0.85rem; color:var(--text-color); opacity:0.75; margin-top:4px;">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_display_value(value: object) -> str:
    if isinstance(value, dict):
        return ', '.join(f"{key}: {item}" for key, item in value.items() if item is not None)
    if isinstance(value, list):
        return '; '.join(str(item) for item in value)
    return str(value)


def sanitize_label(value: object, fallback: str = 'Day') -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        text = value.strip()
        return text or fallback
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, dict)):
        return format_display_value(value)
    return str(value)


st.title('✈️ VoyageAI')
st.caption('A conversational travel planner that helps you discover, organize, and budget your next trip.')

with st.sidebar:
    st.header('Traveler Profile')
    nationality = st.selectbox('Nationality', ['Indian', 'American', 'British', 'Australian', 'Other'])
    currency = st.selectbox('Currency', ['INR', 'USD', 'EUR', 'GBP', 'JPY'])
    travelers = st.number_input('Travelers', min_value=1, max_value=10, value=1)
    duration = st.number_input('Days', min_value=1, max_value=30, value=5)
    budget = st.number_input('Budget', min_value=0.0, value=150000.0, step=500.0)
    travel_dates = st.text_input('Travel dates (YYYY-MM-DD)', '')
    transport_pref = st.selectbox('Preferred transportation', ['flight', 'train', 'car', 'bus', 'flexible'])
    accommodation_pref = st.selectbox('Preferred accommodation', ['budget', 'moderate', 'premium', 'luxury'])
    season = st.selectbox('Travel season', ['summer', 'winter', 'spring', 'autumn', 'monsoon', 'flexible'])
    interests = st.multiselect('Interests', ['adventure', 'nature', 'beaches', 'trekking', 'shopping', 'food', 'nightlife', 'history', 'culture', 'wildlife', 'photography', 'luxury', 'family', 'honeymoon', 'solo'])

sample_prompts = [
    'Plan a 5-day trip to Kashmir under ₹50,000 for a couple with food and nature interests.',
    'Plan a 7-day honeymoon in Bali with a budget of ₹2,00,000.',
    'Suggest a solo backpacking trip to Vietnam under ₹80,000.',
]

st.markdown('Try one of these sample prompts:')
cols = st.columns(3)
for col, prompt in zip(cols, sample_prompts):
    if col.button(prompt[:34] + '…', use_container_width=True):
        st.session_state.user_input = prompt

user_input = st.text_area('Travel request', height=140, key='user_input', placeholder='Example: Plan a 10-day Europe trip for a family of four in summer with culture and beach stops.')

if st.button('Generate Travel Plan', use_container_width=True):
    if not user_input.strip():
        st.error('Please enter a travel request.')
    else:
        st.session_state.messages.append({'role': 'user', 'content': user_input})
        user_profile = {
            'nationality': nationality,
            'currency': currency,
            'travelers': travelers,
            'duration': duration,
            'budget': budget,
            'travel_dates': travel_dates or None,
            'preferred_transportation': transport_pref if transport_pref != 'flexible' else None,
            'preferred_accommodation': accommodation_pref if accommodation_pref != 'moderate' else None,
            'travel_season': season if season != 'flexible' else None,
            'interests': interests,
        }
        with st.spinner('Coordinating your travel plan...'):
            result = st.session_state.supervisor.handle_request(user_input, user_profile)
        st.session_state.latest_result = result
        destination = result.get('destination_recommendations', [{}])[0] if result.get('destination_recommendations') else {}
        st.session_state.messages.append({'role': 'assistant', 'content': f"Your trip to {destination.get('name', 'your destination')} is ready. I’ve put together a tailored itinerary, budget, and travel notes for you."})

if st.session_state.messages:
    st.subheader('Conversation')
    for item in st.session_state.messages:
        render_bubble(item['role'], item['content'])

if st.session_state.latest_result:
    result = st.session_state.latest_result
    destination = result.get('destination_recommendations', [{}])[0] if result.get('destination_recommendations') else {}
    st.subheader('Trip Overview')
    col1, col2, col3 = st.columns(3)
    with col1:
        render_card('Destination', destination.get('name', 'Custom destination'), destination.get('reason', 'Dynamic recommendation'))
    with col2:
        budget_data = result.get('budget', {})
        render_card('Estimated Budget', f"{budget_data.get('total', 'N/A')} {budget_data.get('currency', 'INR')}", 'Includes flights, stay, food, transport, and activities')
    with col3:
        render_card('Trip Length', f"{len(result.get('itinerary', []))} days", 'Structured day-by-day itinerary')

    st.subheader('Itinerary')
    for stop in result.get('itinerary', []):
        label = sanitize_label(stop.get('day'), 'Day')
        with st.expander(label, expanded=False):
            if stop.get('morning'):
                st.write(f"**Morning:** {format_display_value(stop['morning'])}")
            if stop.get('afternoon'):
                st.write(f"**Afternoon:** {format_display_value(stop['afternoon'])}")
            if stop.get('evening'):
                st.write(f"**Evening:** {format_display_value(stop['evening'])}")
            if stop.get('places_to_visit'):
                st.write('**Places to visit:**')
                for place in stop['places_to_visit']:
                    st.write(f"- {format_display_value(place)}")
            if stop.get('stay'):
                st.write(f"**Stay:** {format_display_value(stop['stay'])}")

    st.subheader('Budget & Logistics')
    budget_data = result.get('budget', {})
    breakdown = budget_data.get('breakdown', {})
    st.write(f"**Flights:** {breakdown.get('flights', 'N/A')} {budget_data.get('currency', 'INR')}")
    st.write(f"**Accommodation:** {breakdown.get('accommodation', 'N/A')} {budget_data.get('currency', 'INR')}")
    st.write(f"**Food:** {breakdown.get('food', 'N/A')} {budget_data.get('currency', 'INR')}")
    st.write(f"**Transport:** {breakdown.get('transport', 'N/A')} {budget_data.get('currency', 'INR')}")
    st.write(f"**Activities:** {breakdown.get('activities', 'N/A')} {budget_data.get('currency', 'INR')}")
    if budget_data.get('hotel_suggestions'):
        st.write('**Hotel suggestions:**')
        for hotel in budget_data['hotel_suggestions']:
            st.write(f"- {hotel}")

    st.subheader('Travel Support')
    assistance = result.get('travel_assistance', {})
    st.write(f"**Visa guidance:** {assistance.get('visa_guidance', 'N/A')}")
    st.write(f"**Weather forecast:** {assistance.get('weather_forecast', 'N/A')}")
    st.write(f"**Packing checklist:** {assistance.get('packing_checklist', 'N/A')}")
    st.write(f"**Local transport:** {assistance.get('local_transport', 'N/A')}")
    st.write(f"**Travel tips:** {assistance.get('travel_tips', 'N/A')}")

    st.subheader('Reflection')
    reflection = result.get('reflection', {})
    st.write(reflection.get('summary', ''))
    st.write(f"Confidence score: {reflection.get('confidence_score', 'N/A')}")

    download_lines = []
    for stop in result.get('itinerary', []):
        day_label = sanitize_label(stop.get('day'), 'Day')
        highlights = stop.get('highlights', [])
        if isinstance(highlights, list):
            highlights_text = '; '.join(format_display_value(item) for item in highlights)
        else:
            highlights_text = format_display_value(highlights)
        download_lines.append(f"{day_label}: {highlights_text}")

    st.download_button(
        label='Download itinerary summary',
        data='\n'.join(download_lines),
        file_name='itinerary.txt',
        mime='text/plain',
    )
