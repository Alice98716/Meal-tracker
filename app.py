import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. Configuration & Authentication ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Please set your GEMINI_API_KEY in the Streamlit secrets.toml file (or Streamlit Cloud Secrets).")
    st.stop()

model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. Frontend UI ---
st.title("📸 AI Meal Tracker")

# Create tabs for different input methods
tab1, tab2 = st.tabs(["📷 Camera (Food or Label)", "✍️ Written Description"])

# Define the master prompt we will use for the AI
system_prompt = """
You are an expert nutritionist. Analyze the provided food information.
If it is an image, it might be a picture of a meal, a nutrition label, a barcode, or a QR code on packaging. 
If it is text, it is a description of a meal.
Based on the information, estimate the portion sizes and provide the following:
- Total Calories
- Protein (g)
- Carbohydrates (g)
- Fat (g)
Keep the response concise, friendly, and formatted clearly.
"""

# --- TAB 1: Camera Input ---
with tab1:
    st.write("Snap a photo of your food, its nutrition label, or a QR/barcode.")
    picture = st.camera_input("Log your meal")
    
    if picture is not None:
        img = Image.open(picture)
        with st.spinner("Analyzing your image..."):
            try:
                response = model.generate_content([system_prompt, img])
                st.success("Analysis Complete!")
                st.subheader("Estimated Nutrition")
                st.write(response.text)
            except Exception as e:
                st.error(f"An error occurred: {e}")

# --- TAB 2: Text Description ---
with tab2:
    st.write("Don't have a photo? Describe what you ate in detail.")
    food_description = st.text_area(
        "Description", 
        placeholder="e.g., A large bowl of oatmeal with a handful of blueberries, a tablespoon of honey, and black coffee."
    )
    
    # We use a button here so it doesn't try to analyze while you are still typing
    if st.button("Analyze Description"):
        if food_description.strip() == "":
            st.warning("Please enter a description first.")
        else:
            with st.spinner("Calculating macros from your description..."):
                try:
                    # Combine the system instructions with the user's text
                    full_prompt = f"{system_prompt}\n\nUser's meal description: {food_description}"
                    response = model.generate_content(full_prompt)
                    
                    st.success("Analysis Complete!")
                    st.subheader("Estimated Nutrition")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

            
