import streamlit as st
from openai import OpenAI
from supabase import create_client
import json

if "messages" not in st.session_state:
    st.session_state.messages = []
if "lesson_state" not in st.session_state:
    st.session_state.lesson_state = {
        "active": False,
        "current_lesson": 1,
        "current_phase": "introduction",  # New: track the current phase
        "lessons_completed": False,
        "understanding_check": False,
        "understanding_confirmed": False  
    }
if "instructions" not in st.session_state:
    st.session_state.instructions = []
if "openai_initialized" not in st.session_state:
    st.session_state.openai_initialized = False
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "lesson_history" not in st.session_state:
    st.session_state.lesson_history = {}  # Track which lessons have been completed
if "client" not in st.session_state:
    st.session_state.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    st.session_state.openai_initialized = True

# --- FUNCTIONS ---
def init_supabase():
    url = st.secrets["SUPABASE_URL"] 
    key = st.secrets["SUPABASE_KEY"] 
    return create_client(url, key)

def get_phase_prompt(phase, topic, lesson_number, student_input=None):
    """Generate a phase-specific prompt based on the current learning phase."""
    
    # Check if this lesson has been taught before
    previous_lesson_exists = False
    if lesson_number > 1 and f"lesson_{lesson_number-1}" in st.session_state.lesson_history:
        previous_lesson_exists = True
    
    if phase == "introduction":
        prompt = f"""You are teaching {topic} in lesson {lesson_number}. 
        This is the INTRODUCTION phase of the lesson.
        
        Your goal is to:
        1. Briefly introduce the topic to the student.
        2. Ask if they have any prior knowledge about the topic. Ask them a topic-related question
        3. Hence, check for understanding to confirm they're ready to move forward.
        
        RESPONSE FORMAT:
        - Keep your response under 150 words
        - Provide a brief, engaging introduction to {topic}
        - End by testing if they have any prior knowledge or if they're ready to learn about {topic}
        - Do NOT assume any previous knowledge unless confirmed by the student
        
        {"If this is not the first lesson, briefly reference what was covered in the previous lesson." if previous_lesson_exists else ""}
        """
    
    elif phase == "core_content":
        prompt = f"""You are teaching {topic} in lesson {lesson_number}. 
        This is the CORE CONTENT phase of the lesson.
        
        The student's response about their prior knowledge was: "{student_input}"
        
        Your goal is to:
        1. Dive deeper into the topic based on their level of understanding.
        2. Provide clear explanations and connect to real-world examples.
        3. Constantly ask follow-up questions to keep the student interacted
        3. Check for comprehension after explaining the main concepts.
        
        RESPONSE FORMAT:
        - Keep your response under 200 words
        - Explain ONE main concept about {topic} clearly with examples
        - End with a question to check if they understood the explanation
        - Make your explanation age-appropriate for a middle school student
        - If the student responds with a wrong answer, ask them why they think that's the correct answer, keep doing it until they reach correct.
        """
    
    elif phase == "interactive_exercise":
        prompt = f"""You are teaching {topic} in lesson {lesson_number}. 
        This is the INTERACTIVE EXERCISE phase of the lesson.
        
        Your goal is to:
        1. Reinforce the concept through an interactive task or debatable question.
        2. Let the student attempt the task.
        3. Provide appropriate feedback based on their response.
        
        RESPONSE FORMAT:
        - Keep your response under 150 words
        - Create a simple, engaging exercise related to {topic}
        - Make sure the exercise is appropriate for a middle school student
        - The exercise should test understanding of the concept just taught
        - If the student struggles, be prepared to break down the exercise into smaller steps
        - Give the student the option to skip this part and move on
        """
    
    elif phase == "summary":
        prompt = f"""You are teaching {topic} in lesson {lesson_number}. 
        This is the SUMMARY phase of the lesson.
        
        Your goal is to:
        1. Recap the key points covered in this lesson.
        2. Ask the student what they feel were the most important points of the lesson
        3. Suggest what to explore next.
        4. Confirm if the student feels confident to move forward.
        
        RESPONSE FORMAT:
        - Keep your response under 150 words
        - Summarize the main concepts learned about {topic}
        - Suggest a related aspect they could explore in the next lesson
        - End the lesson.
        """
    
    return prompt

def generate_response(prompt, user_input=None):
    """Generate a response based on the given prompt and user input."""
    
    messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.instructions]
    messages_for_api.append({"role": "system", "content": prompt})
    
    # Add the conversation history
    for m in st.session_state.messages:
        messages_for_api.append({"role": m["role"], "content": m["content"]})
    
    # Add the current user input if provided
    if user_input:
        messages_for_api.append({"role": "user", "content": user_input})

    supabse_chat_history = {
        "id": name,
        "messages": st.session_state.messages,
        "topic": st.session_state.topic
    }
    supabase = init_supabase()
    response = supabase.table("chatbot_history").insert(supabse_chat_history).execute()
            


    
    try:
        response = st.session_state.client.chat.completions.create(
            model="gpt-4",
            messages=messages_for_api,
            temperature=1.08,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "I'm having trouble generating content right now. Please try again."



def process_user_input(user_input):
    """Process user input based on the current lesson state."""
    lesson_state = st.session_state.lesson_state
    topic = st.session_state.topic
    
    # If this is the first message, set the topic and start the introduction phase
    if not lesson_state["active"]:
        st.session_state.topic = user_input
        lesson_state["active"] = True
        lesson_state["current_phase"] = "introduction"
        
        # Generate introduction phase content
        prompt = get_phase_prompt("introduction", user_input, lesson_state["current_lesson"])
        response = generate_response(prompt)
        
        # Record that this lesson has started
        lesson_key = f"lesson_{lesson_state['current_lesson']}"
        if lesson_key not in st.session_state.lesson_history:
            st.session_state.lesson_history[lesson_key] = {
                "topic": user_input,
                "phases_completed": ["introduction"]
            }
        
        return response
    
    # Handle progression through phases
    current_phase = lesson_state["current_phase"]
    
    # Check for progression phrases that indicate readiness to move forward
    ready_phrases = ["yes", "ready", "i'm ready", "i am ready", "let's go", "let's continue", 
                     "continue", "next", "yes please", "okay", "ok", "sure", "got it"]
    
    is_ready_response = any(phrase in user_input.lower() for phrase in ready_phrases)
    
    # Handle phase progression
    if current_phase == "introduction" and is_ready_response:
        # Move to core content phase
        lesson_state["current_phase"] = "core_content"
        prompt = get_phase_prompt("core_content", topic, lesson_state["current_lesson"], user_input)
        response = generate_response(prompt)
        
        # Update lesson history
        lesson_key = f"lesson_{lesson_state['current_lesson']}"
        if "core_content" not in st.session_state.lesson_history[lesson_key]["phases_completed"]:
            st.session_state.lesson_history[lesson_key]["phases_completed"].append("core_content")
        
        return response
    
    elif current_phase == "core_content" and is_ready_response:
        # Move to interactive exercise phase
        lesson_state["current_phase"] = "interactive_exercise"
        prompt = get_phase_prompt("interactive_exercise", topic, lesson_state["current_lesson"])
        response = generate_response(prompt)
        
        # Update lesson history
        lesson_key = f"lesson_{lesson_state['current_lesson']}"
        if "interactive_exercise" not in st.session_state.lesson_history[lesson_key]["phases_completed"]:
            st.session_state.lesson_history[lesson_key]["phases_completed"].append("interactive_exercise")
        
        return response
    
    elif current_phase == "interactive_exercise" and is_ready_response:
        # Move to summary phase
        lesson_state["current_phase"] = "summary"
        prompt = get_phase_prompt("summary", topic, lesson_state["current_lesson"])
        response = generate_response(prompt)
        
        # Update lesson history
        lesson_key = f"lesson_{lesson_state['current_lesson']}"
        if "summary" not in st.session_state.lesson_history[lesson_key]["phases_completed"]:
            st.session_state.lesson_history[lesson_key]["phases_completed"].append("summary")
        
        return response
    
    elif current_phase == "summary" and is_ready_response:
        # Complete this lesson and prepare for the next one
        if lesson_state["current_lesson"] < 4:
            lesson_state["current_lesson"] += 1
            lesson_state["current_phase"] = "introduction"
            
            # Start the next lesson
            prompt = get_phase_prompt("introduction", topic, lesson_state["current_lesson"])
            response = generate_response(prompt)
            
            # Record that this new lesson has started
            lesson_key = f"lesson_{lesson_state['current_lesson']}"
            if lesson_key not in st.session_state.lesson_history:
                st.session_state.lesson_history[lesson_key] = {
                    "topic": topic,
                    "phases_completed": ["introduction"]
                }
            
            return response
        else:
            # All lessons completed
            lesson_state["lessons_completed"] = True
            return "Congratulations! You've completed all the lessons on this topic. Is there anything specific you'd like to review or a new topic you'd like to explore?"
    
    # For any other message within a phase, generate a contextual response
    prompt = get_phase_prompt(current_phase, topic, lesson_state["current_lesson"], user_input)
    return generate_response(prompt, user_input)

# --- MAIN APP BODY ---

# Branding and Intro
st.title("MindPath: STEM AI Tutor") 
st.header("Let's make STEM learning fun by AI-Powered tutoring!")
st.markdown("<span style='color:purple'>A Socratic Method Based AI Tutor for Middle Schoolers</span>", unsafe_allow_html=True)

# Sidebar: OpenAI API key input


# Debugging section in sidebar (can be removed in production)
if st.sidebar.checkbox("Show Debug Info"):
    st.sidebar.write("Current Phase:", st.session_state.lesson_state["current_phase"])
    st.sidebar.write("Current Lesson:", st.session_state.lesson_state["current_lesson"])
    st.sidebar.write("Lesson History:", st.session_state.lesson_history)
    st.sidebar.write("Number of Messages:", len(st.session_state.messages))

# User Inputs
name = st.text_input("What's your Student ID?")
if name:
    st.write(f"Hi {name}!")
    st.subheader(f"Hello from your AI Tutor, {name}! Here's how to learn with me:")
    st.markdown("""
1. **Select** your **age** and **grade** in the text boxes below. 
2. **Click the checkbox** below when you're ready to start learning. 
3. **Enter a topic** you want to learn about in the text box.  
4. The chatbot will provide an **explanation** and guide you **step by step**.  
5. Feel free to **ask questions** for clarification.  
6. Once you're ready, take a **quiz** to test your understanding!  
""")
    st.info(f"💡 Tip: **{name}** if you get stuck, try asking the chatbot for **examples** or a simpler explanation!")

# Age and Grade Input
age = st.text_input("What is your age group?")
grade = st.text_input("What grade are you in?")

# Set up tutor system message
if age and grade and name and st.session_state.openai_initialized:
    if not st.session_state.instructions:
        teacher = f"""You are a helpful tutor who specialises in teaching younger kids from grade 6-9 STEM topics. 
You are going to be engaging and will ask cross-questions to the student to help them answer the question. 
You are encouraging and motivating. You will make sure you help students get to the answer rather than give it out! 
You will break down the topic they are learning and ask questions after each part to move on. 
You will be patient and flexible to their learning style. 
You will apply the STEM topics to real world scenarios and teach the students. 
You will give the students tasks to do in which they can replicate the topic learned in real life as a tutor.
If the students give out a wrong answer, you will tell them and then help them reach the right answer."""
        
        st.session_state.instructions = [
            {"role": "system", "content": teacher + " you are teaching " + name + " who is " + str(age) + " years old and studies in grade " + str(grade)},
            {"role": "system", "content": "You are a knowledgeable tutor."}
        ]

# Learning Start
ready = st.checkbox("I'm ready to start learning!")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Handle user input and generate responses
if ready and st.session_state.openai_initialized:
    user_input = st.chat_input("What are we learning today?")
    
    if user_input:
        # Display the user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Add the message to session state
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.spinner("Thinking..."):
            # Process the user input and get a response
            response = process_user_input(user_input)
            
            # Add and display the response
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.write(response)
        
        # File upload for assignments
        uploaded_file = st.file_uploader("Upload your work and get feedback or ask visual questions!", key=f"file_upload_{len(st.session_state.messages)}")
        if uploaded_file is not None:
            # Handle uploaded file
            st.success("File uploaded successfully! The tutor will review it.")
            # You can add code here to process the file if needed

# Insert student info into Supabase
if name and age and grade and st.session_state.openai_initialized:
    if "student_info_inserted" not in st.session_state:
        try:
            st.session_state.student_info = {
                "id": name,
                "age": age,
                "grade": grade
            }
            supabase = init_supabase()
            response = supabase.table("student info").insert(st.session_state.student_info).execute()
            st.session_state.student_info_inserted = True
            st.sidebar.success("Student information saved successfully!")
        except Exception as e:
            st.sidebar.error(f"Error saving student information: {str(e)}")


    
