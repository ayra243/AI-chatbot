
import random
import openai
import streamlit as st
from supabase import create_client
import json 



if "quiz_id" not in st.session_state:
    st.session_state.quiz_id = []
if "quiz_bank" not in st.session_state:
    st.session_state.quiz_bank = {}  # Stores all quizzes
if "current_quiz" not in st.session_state:
    st.session_state.current_quiz = None  # Active quiz session
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

def init_supabase():
    url = st.secrets["SUPABASE_URL"] 
    key = st.secrets["SUPABASE_KEY"] 
    return create_client(url, key)




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
        response = supabase.table("Quiz student id").insert(st.session_state.quiz_info).execute()
        create_quiz(difficulty, topic) 
        st.session_state.taking_quiz = True
    else:
        st.error("missing the difficulty level")


def create_quiz(quiz_difficulty, topic):
    """Generate a quiz based on user-selected difficulty and topic."""
    
    quiz_id = random.randint(1, 10000)
    while quiz_id in st.session_state.quiz_id:  # Ensure uniqueness
        quiz_id = random.randint(1, 10000)

    st.session_state.quiz_id.append(quiz_id)  # Store quiz ID

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
    question_json = json.dumps(quiz_questions)
    supabase_json = {
        "quiz_id": quiz_id,
        "topic": topic,
        "difficulty": quiz_difficulty,
        "questions": question_json
    }
    supabase = init_supabase()
    response = supabase.table("quiz database").insert(supabase_json).execute()
    st.session_state.current_quiz = quiz_id

    return quiz_questions


def create_question(quiz_id, quiz_difficulty, topic, question_format):
    """Generate quiz questions based on difficulty."""
    
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"]) 
    #  quiz questions
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": f"The student wants a {quiz_difficulty} quiz on {topic}. "
                                        f"Generate 10 questions using this format: {question_format}. Make sure you don't generate all the questions at once. "
                                        "Ensure they match the difficulty level. End each question with π. Make sure you don't give the answer"},
            {"role": "system", "content": "You are an AI teacher generating educational quizzes"}
        ],
        temperature=1.08, max_tokens=550, top_p=1, frequency_penalty=0, presence_penalty=0
    )
    quiz_questions = response.choices[0].message.content


    return quiz_questions

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
    """Retrieve a quiz from the quiz bank using its ID."""
    return st.session_state.quiz_bank.get(quiz_id, "Quiz not found!")

def answers_move_on():
    st.session_state.current_answer_index += 1
    st.session_state.AI_feedback = ""

def answers_move_back():
    st.session_state.current_answer_index -= 1
    st.session_state.AI_feedback = ""

def need_help_button():
    st.session_state.need_help_counter += 1
    supabase_json = {
        "QUIZ_ID":  st.session_state.current_quiz,
        "student id": st.session_state.quiz_info["name"],
        "need_help_counter": st.session_state.need_help_counter
    }

    supabase = init_supabase()
    response = supabase.table("answer table").insert(supabase_json).execute()
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"]) 
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": f"The student needs further help on this question {st.session_state.questions[st.session_state.current_answer_index]}{st.session_state.graded_results[st.session_state.current_answer_index]}"
                                        f"Look through the student's incorrect answer, the correct answer and the feedback you provided, and then find a more detailed and interactive way of explaining"
                                        "Make sure your explanation is detailed and of a different approach from the feedback given"},
            {"role": "system", "content": "You are an AI teacher further explaining questions a student is confused with"}
        ],
        temperature=1.08, max_tokens=550, top_p=1, frequency_penalty=0, presence_penalty=0
    )
    st.session_state.AI_feedback = response.choices[0].message.content
    

def retake_quiz():
    st.session_state.taking_quiz = True
    st.session_state.current_question_index = 0


def load_grading_rubric():

    complete_rubric = """ 
    True/False Questions (Easy)
    Criteria:
    Correct answer → Full credit (1 pt)
    Incorrect answer → No credit (0 pt)
    Fill in the Blanks (Easy)
    Criteria:
    Exact match / minto typo → Full credit (1 pt)
    correct synonym → Partial credit (0.5 pt)
    Wrong or unrelated → No credit
    Multiple Choice Questions (Easy/Medium)
    Single-answer MCQ
    Correct option → Full credit
    Wrong option → No credit
    Short Answer Questions (Medium)
    Includes all key concepts → Full credit (2 pts)
    Includes 50 to 75 percent of key concepts → Partial credit (1 pt)
    Lacks relevant concepts or wrong explanation → No credit


    Long Answer / Explanation Questions (Hard)
    Criteria:
    Clear explanation, all critical points, well-structured → Full credit (3 pts)
    Some key points, but incomplete explanation → Partial credit (2 pts)
    Minor details but missing most keywords → Partial Credit (1 pt)
    Off-topic, missing core understanding → No credit
    Scenario-Based / Problem-Solving Questions (Hard)
    Criteria:
    Correct logic, steps, and conclusion → Full credit (3 pts)


    Correct steps but wrong final answer OR good reasoning with a small mistake → Partial credit (1 or 2 pts)
    Flawed logic, misinterprets scenario → No credit


    """
    return complete_rubric

def extract_answer(clean_answers):
    parts = clean_answers.split('student answer')
    student_answer_part = []
    correct_answer_part = []
    feedback_part = []


def grade_answers(student_answers, rubric, quiz_data):
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"]) 
    response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f"""The student has submitted the quiz, grade it based on the {rubric}.
                The student has these answers: {student_answers} and the questions are from {quiz_data}

                RESPONSE FORMAT:
                At the very end of the quiz, when all the questions hav been reviewed, make sure to give TOTAL_SCORE by student out of total points.
                For each question, return your evaluation in this exact format with the delimiter '|||' between questions: 
                QUESTION_NUMBER: [question number]
                STUDENT_ANSWER: [student's answer]
                CORRECT_ANSWER: [correct answer]
                FEEDBACK: [feedback on their answer]
                SCORE: [score]
                |||
                """},
                                            
                                            
                 {"role": "system", "content": "You are an AI teacher grading quizzes"}
             ],
             temperature=1.08, max_tokens=550, top_p=1, frequency_penalty=0, presence_penalty=0
            
     )
    graded_text = response.choices[0].message.content
    student_answer_part = []
    correct_answer_part = []
    feedback_part = []
    score_part = []
   
    parsed_results = []
    questions = graded_text.split("|||")
    
    for question in questions:
        if not question.strip():
            continue
            
        question_data = {}
        lines = question.strip().split("\n")
        
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                question_data[key] = value
        
        if question_data:
            parsed_results.append(question_data)
            if "STUDENT_ANSWER" in question_data: 
                student_answer_part.append(question_data["STUDENT_ANSWER"])
            if "CORRECT ANSWER" in question_data: 
                correct_answer_part.append(question_data["CORRECT_ANSWER"])
            if "FEEDBACK" in question_data: 
                feedback_part.append(question_data["FEEDBACK"])
            if "SCORE" in question_data: 
                score_part.append(question_data["SCORE"])


    supabase_json = {
        "STUDENT_ANSWER": json.dumps(student_answer_part),
        "CORRECT_ANSWER": json.dumps(correct_answer_part),
        "TOTAL_SCORE": parsed_results[-1],
        "SCORE": json.dumps(score_part),
        "FEEDBACK": json.dumps(feedback_part) ,
        "QUIZ_ID":  st.session_state.current_quiz,
        "student id": st.session_state.quiz_info["name"]
    }

    supabase = init_supabase()
    response = supabase.table("answer table").insert(supabase_json).execute()
    st.session_state.current_quiz = quiz_id
    
    return parsed_results


def submit_button():
    student_answers = st.session_state.student_answer
    quiz_data = retrieve_quiz(st.session_state.current_quiz)
    rubric = load_grading_rubric()
    update_answers()

    graded_results = grade_answers(student_answers, rubric, quiz_data)
    st.session_state.graded_results = graded_results
    st.session_state.taking_quiz = False


    #display_review(graded_results)







st.image("logo_mind.png", width=150)
st.title("MindPath: STEM AI Tutor Quiz") 
st.header("Let's make STEM learning fun by AI-Powered tutoring!")
st.markdown("<span style='color:purple'>A Socratic Method Based AI Tutor for Middle Schoolers</span>", unsafe_allow_html=True)

if not st.session_state.quiz_info:
    st.text_input("What's your student ID?", key="student_name")
    st.selectbox("Choose the level of **difficulty** for the quiz!", [" ", "easy", "medium", "hard"], key="quiz_difficulty")
    st.text_input("What topic do you want the quiz on?", key="topic_main")
    st.button("Generate Quiz", on_click=quiz_button)
else:
    if st.session_state.taking_quiz == True:
        result = st.session_state.quiz_info
        st.write(f"**Name:** {result['name']}  \n**Topic:** {result['topic']}  \n**Difficulty:** {result['difficulty']}")

        quiz_id = st.session_state.current_quiz
        quiz_data = retrieve_quiz(quiz_id)
        st.session_state.questions = quiz_data["questions"].split('π')

        st.subheader("**Questions:**")
        st.markdown(st.session_state.questions[st.session_state.current_question_index])
        st.text_input("Answer here:" , key="answers_student")

        if len(st.session_state.questions) - 2 == st.session_state.current_question_index:
            st.button("Click here to submit quiz", on_click=submit_button)


        col1, col2 = st.columns(2)
        with col1: 
            if st.session_state.current_question_index > 0:
                st.button("previous question", on_click=questions_move_back)
        with col2: 
            if len(st.session_state.questions) - 2 > st.session_state.current_question_index:
                st.button("next question", on_click=questions_move_on)
        st.write(st.session_state.student_answer)

    else:
        st.subheader("We are reviewing question #" + str(st.session_state.current_answer_index + 1))
        st.write(st.session_state.questions[st.session_state.current_answer_index])
        st.write(st.session_state.graded_results[st.session_state.current_answer_index]) 
        col3, col4 = st.columns(2)
        with col3: 
            if st.session_state.current_answer_index > 0:
                st.button("previous answer", on_click=answers_move_back)
        with col4: 
            if len(st.session_state.graded_results) - 1 > st.session_state.current_answer_index:
                st.button("next answer", on_click=answers_move_on)
        if len(st.session_state.graded_results) - 1 == st.session_state.current_answer_index:
            st.button("re-take quiz", on_click=retake_quiz)



            
        st.button("I need help", on_click=need_help_button)
        if st.session_state.AI_feedback:
            st.write(st.session_state.AI_feedback)

        
            


        


