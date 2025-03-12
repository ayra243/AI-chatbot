import streamlit as st
from openai import OpenAI

if "messages" not in st.session_state:
    st.session_state.messages = []


api_key = st.sidebar.text_input("Enter your OpenAI API key", type="password")
if api_key:
    client = OpenAI(api_key=api_key)
else:
    st.warning("Please enter your OpenAI API key to continue.")
    st.stop()

teacher = """You are a helpful tutor who specialises in teaching younger kids from grade 6-9 STEM topics. 
You are going to be engaging and will ask cross-questions to the student to help them answer the question. 
You are encouraging and motivating. You will make sure you help students get to the answer rather than give it out! 
You will break down the topic they are learning and ask questions after each part to move on. 
You will be patient and flexible to their learning style. 
You will apply the STEM topics to real world scenarios and teach the students. 
You will give the students tasks to do in which they can replicate the topic learned in real life as a tutor."""

st.session_state.concepts = ["concept 1", "concept 2", "concept 3"]
current_concept = 0
st.title("MindPath: STEM AI Tutor")
st.header("Let's make STEM learning fun by AI-Powered tutoring!")
st.write("MindPath - A socratic method based AI tutor for middle schoolers~")
st.markdown("<span style='color:purple'>This text is purple</span>", unsafe_allow_html=True)
name = st.text_input("What's your name?")
if name:
    st.write(f"Hello, {name}!")

age = st.slider("What is your age group?",6,20)
st.write(f"Let me teach you according to your age: {age}.")
color = st.color_picker("pick your favorite color!")
st.markdown(
    """
    <style>
        body {
            background-color: {color}
        }
    </style>
    """,
    unsafe_allow_html=True
)
st.session_state.messages.append({"role": "system", "content": "You are a knowledgeable tutor."})
st.session_state.messages.append({"role": "system", "content": f"You are teaching{st.session_state.concepts[current_concept]}"})

user_input = st.chat_input("Type your message here...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    response = client.chat.completions.create(
    model="gpt-4",
    messages = st.session_state.messages,
    temperature=1.08, max_tokens=256,  top_p=1, frequency_penalty=0, presence_penalty=0
)
    chatbot_response = response.choices[0].message.content
    with st.chat_message("system"):
        st.write(chatbot_response)
    student_understanding = st.selectbox(
    "Do you understand?",
    ["","Yes", "No", "A little"]
)
    if  student_understanding == "Yes":
        with st.chat_message("system"):
            st.write("Great! You now understand the concept")
        current_concepts = current_concepts + 1
        st.session_state.messages.append({"role": "system", "content": f"You are teaching{st.session_state.concepts[current_concept]}"})
