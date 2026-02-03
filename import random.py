import random
import openai
import streamlit as st
import json 


# ---------- SUPABASE DISABLED (DO NOT TOUCH APP LOGIC) ----------

class DummySupabase:
    def table(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def execute(self, *args, **kwargs):
        return None


def init_supabase():
    return DummySupabase()

# ---------------------------------------------------------------


if "quiz_id" not in st.session_state:
    st.session_state.quiz_id = []
if "quiz_bank" not in st.session_state:
    st.session_state.quiz_bank = {}
if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = None
if "quiz_info" not in st.session_state:
    st.session_state.quiz_info = None
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "student_answer" not in st.session_state:
    st.session_state.student_answer = []
if "graded_results" not in st.session_state:
    st.session_state.graded_results = None
if "current_answer_index" not in st.session_state:
    st.session_state.current_answer_index = 0
if "need_help_counter" not in st.session_state:
    st.session_state.need_help_counter = 0
if "AI_feedback" not in st.session_state:
    st.session_state.AI_feedback = None
if "taking_quiz" not in st.session_state:
    st.session_state.taking_quiz = False
if "questions" not in st.session_state:
    st.session_state.questions = None


import streamlit as st

if not st.user.is_logged_in:
    st.title("Please log in")
    st.login()
    st.stop()


def basic(name, difficulty, topic):
    st.session_state.quiz_info = {
        "name": name,
        "topic": topic,
        "difficulty": difficulty
    }


def quiz_button(): 
    name = st.session_state.student_name
    difficulty = st.session_state.quiz_difficulty
    topic = st.session_state.topic_main
    if not name or not topic or not difficulty:
        st.error("missing an input, provide all required details")
        return
    if difficulty != " ":
        basic(name, difficulty, topic)
        supabase = init_supabase()
        supabase.table("Quiz student id").insert(st.session_state.quiz_info).execute()
        create_quiz(difficulty, topic) 
        st.session_state.taking_quiz = True
    else:
        st.error("missing the difficulty level")


def create_quiz(quiz_difficulty, topic):
    quiz_id = random.randint(1, 10000)
    while quiz_id in st.session_state.quiz_id:
        quiz_id = random.randint(1, 10000)

    st.session_state.quiz_id.append(quiz_id)

    question_types = {
        "easy": "True/False, Fill in the Blanks, Simple Multiple-Choice Questions (MCQs).",
        "medium": "MCQs, Short Answer Questions.",
        "hard": "Long Answer Questions, Scenario-Based MCQs, Problem-Solving Questions."
    }

    question_format = question_types.get(quiz_difficulty.lower(), "MCQs")  

    quiz_questions = create_question(quiz_id, quiz_difficulty, topic, question_format)

    st.session_state.quiz_bank[quiz_id] = {
        "quiz_id": quiz_id,
        "topic": topic,
        "difficulty": quiz_difficulty,
        "questions": quiz_questions
    }

    supabase_json = {
        "quiz_id": quiz_id,
        "topic": topic,
        "difficulty": quiz_difficulty,
        "questions": json.dumps(quiz_questions)
    }

    supabase = init_supabase()
    supabase.table("quiz database").insert(supabase_json).execute()

    st.session_state.current_quiz = quiz_id
    return quiz_questions


def create_question(quiz_id, quiz_difficulty, topic, question_format):
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"]) 

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": f"The student wants a {quiz_difficulty} quiz on {topic}. "
                                        f"Generate 10 questions using this format: {question_format}. "
                                        "End each question with π. Make sure you don't give the answer"},
            {"role": "system", "content": "You are an AI teacher generating educational quizzes"}
        ],
        temperature=1.08,
        max_tokens=550
    )
    return response.choices[0].message.content


def update_answers(): 
    while len(st.session_state.student_answer) <= st.session_state.current_question_index:
        st.session_state.student_answer.append("")
    st.session_state.student_answer[st.session_state.current_question_index] = st.session_state.answers_student
    st.session_state.answers_student = ""


def questions_move_on():
    update_answers()
    st.session_state.current_question_index += 1


def questions_move_back():
    update_answers()
    st.session_state.current_question_index -= 1


def retrieve_quiz(quiz_id):
    return st.session_state.quiz_bank.get(quiz_id, "Quiz not found!")


def answers_move_on():
    st.session_state.current_answer_index += 1
    st.session_state.AI_feedback = ""


def answers_move_back():
    st.session_state.current_answer_index -= 1
    st.session_state.AI_feedback = ""


def need_help_button():
    st.session_state.need_help_counter += 1

    supabase = init_supabase()
    supabase.table("answer table").insert({
        "QUIZ_ID": st.session_state.current_quiz,
        "student id": st.session_state.quiz_info["name"],
        "need_help_counter": st.session_state.need_help_counter
    }).execute()

    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"]) 
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Explain this question again in a clearer way."},
            {"role": "system", "content": "You are an AI teacher further explaining questions"}
        ],
        temperature=1.08,
        max_tokens=550
    )
    st.session_state.AI_feedback = response.choices[0].message.content


# ---------------- UI (UNCHANGED) ---------------- #

st.image("logo_mind.png", width=150)
st.title(" STEM-AI Tutor Quiz") 
st.header("Let's make STEM learning fun by AI-Powered tutoring!")
st.markdown("<span style='color:purple'>IB Learning made easier</span>", unsafe_allow_html=True)
