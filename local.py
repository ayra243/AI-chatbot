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
        st.info("Please write it down and keep it safe! You need it throughout!!")

# Step 2 - Pre-Quiz Website
if st.session_state.student_id and not st.session_state.quiz_completed:
    st.header("Step 2 - Take Your First Quiz!")
    st.markdown("""
    Go to the pre-quiz website.  
    **Choose a topic you have little or no prior knowledge of.**  
    **Enter your Student ID** when asked on the site.
    """)
    st.link_button("Go to Quiz Website", "https://ai-chatbot-grvylr92fzxeyht8awdhia.streamlit.app/")
    st.session_state.quiz_completed = True  # Mark quiz as completed after the link is clicked

# Step 3 - After Quiz, Return to Page
if st.session_state.quiz_completed and not st.session_state.chatbot_completed:
    st.header("Step 3: Return to This Page")
    st.markdown("Make sure you don't cross this tab. Return here once you've completed the quiz")

# Step 4 - AI Chatbot
if st.session_state.quiz_completed and not st.session_state.chatbot_completed:
    st.header("Step 4: Learn with the AI Chatbot")
    st.markdown(f"""
    Go to the AI-powered chatbot and use the **same Student ID**: `{st.session_state.student_id}`  
    Learn about the **same topic** you selected in the pre-quiz.  
    Follow all instructions on the chatbot site.
    """)
    st.link_button("Go to Chatbot", "https://ai-chatbot-h5ltq4kyzrgrxgrug4bnbv.streamlit.app/")
    st.session_state.chatbot_completed = True  # Mark chatbot as completed after the link is clicked

# Step 5 & 6 - Return Again & Post-Quiz
if st.session_state.chatbot_completed:
    st.header("Step 5: Return Again")
    st.markdown("After you've explored the AI chatbot, come back here for the final quiz. (Keep this tab)")

    st.header("Step 6: Take the Post-Quiz & Feedback Survey")
    st.markdown("""
    Take the final quiz, then complete a short survey (return to this tab after the quiz for survey).  
    **Use your Student ID again** when asked.
    """)
    st.link_button("Go to Quiz", "https://ai-chatbot-grvylr92fzxeyht8awdhia.streamlit.app/")
    st.link_button("Survey", "https://docs.google.com/forms/d/e/1FAIpQLScWdeBLpsjYMI1UKbqRIeL_ywOuMwuaS1oH20Ww8Q4KmncOJQ/viewform?usp=header")

# Footer
st.markdown("---")
st.caption("**This process is part of a research or educational program. Please follow all steps completely.**")

