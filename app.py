import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
from datetime import datetime

# --- 1. Configuration & Authentication ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Please set your GEMINI_API_KEY in the Streamlit secrets.")
    st.stop()

# Use flash for speed and reliability
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. Daily Tracking & History Setup (Session State) ---
# Expanded to include detailed micronutrients
if 'daily_totals' not in st.session_state:
    st.session_state.daily_totals = {
        "calories": 0, "protein": 0, "carbs": 0, "fat": 0,
        "fiber": 0, "sugar": 0, "sodium": 0, "cholesterol": 0
    }

# New: Keep track of individual meals
if 'meal_history' not in st.session_state:
    st.session_state.meal_history = []

# FDA General Daily Recommended Values (Based on a standard 2000 cal diet)
DAILY_GOALS = {
    "calories": 2000,
    "protein": 50,     # g
    "carbs": 275,      # g
    "fat": 78,         # g
    "fiber": 28,       # g
    "sugar": 50,       # g (Limit)
    "sodium": 2300,    # mg (Limit)
    "cholesterol": 300 # mg (Limit)
}

# --- 3. Main Application Structure ---
st.title("🥗 AI Macro Tracker")

# Two main tabs to act as pages
main_tab, history_tab = st.tabs(["📊 Dashboard & Logging", "🗓️ Meal Diary"])

def calc_progress(current, goal):
    """Prevents the progress bar from crashing if you go over 100%"""
    return min(current / goal, 1.0)

# --- 4. The AI Processing Logic ---
system_prompt = """
You are an expert nutritionist. Analyze the provided food images or text description.
Estimate the nutritional value for the ENTIRE meal represented. Give the meal a short, descriptive name.
You MUST respond ONLY with a valid JSON object. Do not include markdown formatting like ```json.
Format the JSON exactly like this:
{"name": "Short meal name", "calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0, "sugar": 0, "sodium": 0, "cholesterol": 0}
"""

def process_meal(contents_to_analyze, source_type):
    with st.spinner("Analyzing nutrients..."):
        try:
            # Send the data to Gemini
            response = model.generate_content([system_prompt] + contents_to_analyze)
            
            # Clean up the response to ensure it's pure JSON
            raw_text = response.text.replace("```json", "").replace("```", "").strip()
            nutrition_data = json.loads(raw_text)
            
            # 1. Update the daily totals
            for key in st.session_state.daily_totals.keys():
                st.session_state.daily_totals[key] += nutrition_data.get(key, 0)
            
            # 2. Add to the history diary
            st.session_state.meal_history.append({
                "time": datetime.now().strftime("%I:%M %p"),
                "name": nutrition_data.get("name", "Unknown Meal"),
                "type": source_type,
                "data": nutrition_data
            })
            
            st.success(f"Added {nutrition_data.get('name', 'Meal')}! (+{nutrition_data.get('calories', 0)} kcal)")
        except Exception as e:
            st.error(f"Could not calculate nutrients. Make sure the image is clear. Error: {e}")

# --- 5. Dashboard & Logging UI ---
with main_tab:
    st.header("Today's Summary")
    
    # --- Energy Bar ---
    cals = st.session_state.daily_totals['calories']
    st.metric("Energy (Calories)", f"{cals} / {DAILY_GOALS['calories']} kcal")
    st.progress(calc_progress(cals, DAILY_GOALS['calories']))
    
    st.divider()
    
    # --- Macronutrients ---
    st.subheader("Macronutrients")
    mac1, mac2, mac3 = st.columns(3)
    with mac1:
        st.caption(f"Protein ({st.session_state.daily_totals['protein']}g / {DAILY_GOALS['protein']}g)")
        st.progress(calc_progress(st.session_state.daily_totals['protein'], DAILY_GOALS['protein']))
    with mac2:
        st.caption(f"Carbs ({st.session_state.daily_totals['carbs']}g / {DAILY_GOALS['carbs']}g)")
        st.progress(calc_progress(st.session_state.daily_totals['carbs'], DAILY_GOALS['carbs']))
    with mac3:
        st.caption(f"Fat ({st.session_state.daily_totals['fat']}g / {DAILY_GOALS['fat']}g)")
        st.progress(calc_progress(st.session_state.daily_totals['fat'], DAILY_GOALS['fat']))

    st.write("") # Spacer

    # --- Micronutrients & Limits ---
    st.subheader("Micronutrients & Limits")
    mic1, mic2 = st.columns(2)
    with mic1:
        st.caption(f"Fiber ({st.session_state.daily_totals['fiber']}g / {DAILY_GOALS['fiber']}g)")
        st.progress(calc_progress(st.session_state.daily_totals['fiber'], DAILY_GOALS['fiber']))
        
        st.caption(f"Sodium ({st.session_state.daily_totals['sodium']}mg / {DAILY_GOALS['sodium']}mg)")
        st.progress(calc_progress(st.session_state.daily_totals['sodium'], DAILY_GOALS['sodium']))
    with mic2:
        st.caption(f"Sugar ({st.session_state.daily_totals['sugar']}g / {DAILY_GOALS['sugar']}g limit)")
        st.progress(calc_progress(st.session_state.daily_totals['sugar'], DAILY_GOALS['sugar']))
        
        st.caption(f"Cholesterol ({st.session_state.daily_totals['cholesterol']}mg / {DAILY_GOALS['cholesterol']}mg limit)")
        st.progress(calc_progress(st.session_state.daily_totals['cholesterol'], DAILY_GOALS['cholesterol']))
        
    st.divider()
    
    # --- Add Meal Section ---
    st.subheader("➕ Log a Meal")
    log_type = st.radio("Choose input method:", ["📷 Photo/Label", "✍️ Written Description"], horizontal=True)
    
    if log_type == "📷 Photo/Label":
        uploaded_files = st.file_uploader("Upload or take photos", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        if uploaded_files and st.button("Analyze Photos", use_container_width=True):
            images = [Image.open(file) for file in uploaded_files]
            process_meal(images, "Photo")
    else:
        food_description = st.text_area("What did you eat?", placeholder="e.g., 2 scrambled eggs, a slice of toast, and an apple.")
        if st.button("Analyze Description", use_container_width=True):
            if food_description.strip():
                process_meal([food_description], "Text Description")
            else:
                st.warning("Please type a description first.")

# --- 6. Meal Diary / History UI ---
with history_tab:
    st.header("📖 Today's Diary")
    
    if len(st.session_state.meal_history) == 0:
        st.info("No meals logged yet today.")
    else:
        # Loop through history in reverse (newest at the top)
        for i, meal in enumerate(reversed(st.session_state.meal_history)):
            # The first (most recent) item will be expanded by default
            m_data = meal['data']
            title = f"{meal['time']} - {meal['name']} ({m_data.get('calories', 0)} kcal)"
            
            with st.expander(title, expanded=(i == 0)):
                st.caption(f"Logged via: {meal['type']}")
                
                # Show mini-breakdown for this specific meal
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Protein", f"{m_data.get('protein', 0)}g")
                c2.metric("Carbs", f"{m_data.get('carbs', 0)}g")
                c3.metric("Fat", f"{m_data.get('fat', 0)}g")
                c4.metric("Fiber", f"{m_data.get('fiber', 0)}g")
                
                c5, c6 = st.columns(2)
                c5.metric("Sugar", f"{m_data.get('sugar', 0)}g")
                c6.metric("Sodium", f"{m_data.get('sodium', 0)}mg")
