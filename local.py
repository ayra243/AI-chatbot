import random
import openai
import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

#client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY')) 
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])  


def get_student_id_from_openai():
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Generate a random unique 3-digit student ID in the format STU-XXX."},
            {"role": "user", "content": "Generate a student ID."}
        ]
    )
    return response.choices[0].message.content.strip()

st.image("logo_mind.png", width=150)
st.title("MindPath Instruction Guide") 

# Step 1 - Generate Student ID
if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "quiz_completed" not in st.session_state:
    st.session_state.quiz_completed = False
if "chatbot_completed" not in st.session_state:
    st.session_state.chatbot_completed = False

if st.session_state.student_id is None:
    st.header("Step 1 - Generate your student ID")
    student_ID = st.button("Generate Student ID")
    if student_ID:
        with st.spinner("Generating..."):
            st.session_state.student_id = get_student_id_from_openai()
        st.success(f"Your Student ID: **{st.session_state.student_id}**")
        

# Step 2 - Pre-Quiz Website
if st.session_state.student_id and not st.session_state.quiz_completed:
    st.header("Take Your Quiz!")
    st.link_button("Go to Quiz Website", "https://ai-chatbot-grvylr92fzxeyht8awdhia.streamlit.app/")
    st.session_state.quiz_completed = True  # Mark quiz as completed after the link is clicked

# Step 4 - AI Chatbot
if st.session_state.quiz_completed and not st.session_state.chatbot_completed:
    st.header("Step 4:- Learn with the AI Chatbot")

    st.link_button("Go to Chatbot", "https://mindpath.streamlit.app/")
    st.session_state.chatbot_completed = True  # Mark chatbot as completed after the link is clicked

