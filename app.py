import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# --- 1. Configuration & Authentication ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Please set your GEMINI_API_KEY in the Streamlit secrets.")
    st.stop()

# We use the pro model here as it is better at strict data formatting, but flash still works!
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. Daily Tracking Setup (Session State) ---
# This keeps track of your numbers as long as the tab is open
if 'daily_totals' not in st.session_state:
    st.session_state.daily_totals = {
        "calories": 0, 
        "protein": 0, 
        "carbs": 0, 
        "fat": 0
    }

# FDA General Daily Recommended Values (Based on a 2000 calorie diet)
DAILY_GOALS = {
    "calories": 2000,
    "protein": 50,   # grams
    "carbs": 275,    # grams
    "fat": 78        # grams
}

# --- 3. Frontend UI: The Dashboard ---
st.title("🥗 AI Meal & Macro Tracker")

st.subheader("📊 Your Daily Progress")
col1, col2, col3, col4 = st.columns(4)

# Helper function to safely calculate progress bar percentage (max 1.0)
def calc_progress(current, goal):
    return min(current / goal, 1.0)

with col1:
    st.metric("Calories", f"{st.session_state.daily_totals['calories']} / {DAILY_GOALS['calories']}")
    st.progress(calc_progress(st.session_state.daily_totals['calories'], DAILY_GOALS['calories']))

with col2:
    st.metric("Protein (g)", f"{st.session_state.daily_totals['protein']} / {DAILY_GOALS['protein']}")
    st.progress(calc_progress(st.session_state.daily_totals['protein'], DAILY_GOALS['protein']))

with col3:
    st.metric("Carbs (g)", f"{st.session_state.daily_totals['carbs']} / {DAILY_GOALS['carbs']}")
    st.progress(calc_progress(st.session_state.daily_totals['carbs'], DAILY_GOALS['carbs']))

with col4:
    st.metric("Fat (g)", f"{st.session_state.daily_totals['fat']} / {DAILY_GOALS['fat']}")
    st.progress(calc_progress(st.session_state.daily_totals['fat'], DAILY_GOALS['fat']))

st.divider()

# --- 4. The AI Processing Logic ---
system_prompt = """
You are an expert nutritionist. Analyze the provided food images (meals, QR codes, or labels) or text description.
Estimate the total nutritional value for the ENTIRE meal represented.
You MUST respond ONLY with a valid JSON object in this exact format, with no other text, markdown, or explanation:
{"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
"""

def process_meal(contents_to_analyze):
    with st.spinner("Analyzing nutrients..."):
        try:
            # Send the data to Gemini
            response = model.generate_content([system_prompt] + contents_to_analyze)
            
            # Clean up the response to ensure it's pure JSON
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            nutrition_data = json.loads(raw_text)
            
            # Update the session state with the new numbers
            st.session_state.daily_totals["calories"] += nutrition_data.get("calories", 0)
            st.session_state.daily_totals["protein"] += nutrition_data.get("protein", 0)
            st.session_state.daily_totals["carbs"] += nutrition_data.get("carbs", 0)
            st.session_state.daily_totals["fat"] += nutrition_data.get("fat", 0)
            
            st.success(f"Added! (+{nutrition_data.get('calories')} kcal)")
            # Rerun the app to update the dashboard charts
            st.rerun()
            
        except Exception as e:
            st.error(f"Could not calculate nutrients. Make sure the image is clear. Error: {e}")

# --- 5. Frontend UI: Input Methods ---
tab1, tab2 = st.tabs(["📷 Upload/Take Photos", "Write Description"])

with tab1:
    st.info("Tap 'Browse files' below. On your phone, select 'Camera' to take pictures (front or back!), or select multiple photos from your gallery.")
    uploaded_files = st.file_uploader("Log your meal", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files and st.button("Analyze Photos"):
        images = [Image.open(file) for file in uploaded_files]
        process_meal(images)

with tab2:
    food_description = st.text_area("What did you eat?", placeholder="e.g., 2 scrambled eggs, a slice of toast, and an apple.")
    
    if st.button("Analyze Description"):
        if food_description.strip():
            process_meal([food_description])
        else:
            st.warning("Please type a description first.")
