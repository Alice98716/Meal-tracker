import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. Configuration & Authentication ---
# We use Streamlit Secrets to securely store your API key.
# Create a folder named .streamlit, and inside it, a file named secrets.toml 
# Add this line to secrets.toml: GEMINI_API_KEY = "your_actual_api_key_here"

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("Please set your GEMINI_API_KEY in the Streamlit secrets.toml file.")
    st.stop()

# Initialize the model (Gemini 2.5 Flash is ideal for fast, free-tier image analysis)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. Frontend UI ---
st.title("📸 AI Meal Tracker")
st.write("Snap a photo of your food to get its nutritional breakdown.")

# This single line creates the camera widget on mobile and desktop
picture = st.camera_input("Log your meal")

# --- 3. Processing the Image ---
if picture is not None:
    # Convert the captured byte data into a PIL Image object
    img = Image.open(picture)
    
    with st.spinner("Analyzing your meal..."):
        try:
            # Define the instructions for the AI
            prompt = """
            You are an expert nutritionist. Analyze the food in this image.
            Estimate the portion sizes and provide the following:
            - Total Calories
            - Protein (g)
            - Carbohydrates (g)
            - Fat (g)
            Keep the response concise and formatted clearly.
            """
            
            # Send the text prompt and the image to Gemini
            response = model.generate_content([prompt, img])
            
            # Display the AI's response
            st.subheader("Estimated Nutrition")
            st.write(response.text)
            
        except Exception as e:
            st.error(f"An error occurred while contacting the Gemini API: {e}")
            