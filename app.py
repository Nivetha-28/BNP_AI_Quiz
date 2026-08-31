import os
import json
import streamlit as st
from pypdf import PdfReader
from dotenv import load_dotenv
from google import genai


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Quiz Generator",
    page_icon="🧠",
    layout="centered"
)
# =========================================================
# CUSTOM UI
# =========================================================

st.markdown("""
<style>

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: bold;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    margin-bottom: 30px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# 2. LOAD GEMINI API KEY
# =========================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error(
        "❌ Gemini API key not found. "
        "Please check your .env file."
    )
    st.stop()

client = genai.Client(api_key=api_key)


# =========================================================
# 3. SESSION STATE
# =========================================================

if "quiz" not in st.session_state:
    st.session_state["quiz"] = None

if "quiz_submitted" not in st.session_state:
    st.session_state["quiz_submitted"] = False

if "score" not in st.session_state:
    st.session_state["score"] = 0

if "percentage" not in st.session_state:
    st.session_state["percentage"] = 0

if "difficulty" not in st.session_state:
    st.session_state["difficulty"] = "Medium"

if "time_limit" not in st.session_state:
    st.session_state["time_limit"] = 5


# =========================================================
# 4. TITLE
# =========================================================

st.title("🧠 AI Quiz Generator")

st.write(
    "Upload your study material and let AI "
    "create an interactive quiz!"
)


st.markdown(
    '<div class="subtitle">'
    'Transform your study material into an interactive AI-powered quiz'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# 5. PDF UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "📄 Upload your study material",
    type=["pdf"]
)


# =========================================================
# 6. PROCESS PDF
# =========================================================

if uploaded_file is not None:

    try:

        reader = PdfReader(uploaded_file)

        text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        if not text.strip():

            st.error(
                "❌ Could not extract text from this PDF."
            )

            st.stop()

        st.success(
            "✅ PDF uploaded successfully!"
        )

        # Show extracted text
        with st.expander(
            "📖 View extracted text"
        ):

            st.text_area(
                "PDF Content",
                text,
                height=200
            )

    except Exception as e:

        st.error(
            f"❌ Error reading PDF: {e}"
        )

        st.stop()


    # =====================================================
    # 7. QUIZ SETTINGS
    # =====================================================

    st.subheader("⚙️ Quiz Settings")

    num_questions = st.number_input(
        "🔢 Number of questions",
        min_value=1,
        max_value=10,
        value=5,
        step=1
    )

    difficulty = st.selectbox(
        "🎯 Difficulty",
        ["Easy", "Medium", "Hard"]
    )

    time_limit = st.selectbox(
        "⏱️ Time limit",
        [5, 10, 15, 20],
        format_func=lambda x:
            f"{x} minutes"
    )


    # =====================================================
    # 8. GENERATE QUIZ
    # =====================================================

    if st.button(
        "🤖 Generate Quiz",
        use_container_width=True
    ):

        with st.spinner(
            "🤖 AI is generating your quiz..."
        ):

            prompt = f"""
You are an expert educational quiz generator.

Create exactly {num_questions} multiple-choice
questions using ONLY the study material provided below.

Difficulty level: {difficulty}

Rules:

1. Create exactly {num_questions} questions.
2. Each question must have exactly four options.
3. Options must be A, B, C and D.
4. Only one option can be correct.
5. The answer must be A, B, C or D.
6. Give a short explanation for every answer.
7. Questions must be based ONLY on the study material.
8. Do not invent information.
9. Return ONLY valid JSON.
10. Do not use Markdown.
11. Do not add ```json.
12. Do not add any text before or after the JSON.

Use exactly this structure:

{{
    "questions": [
        {{
            "question": "Question text",
            "options": {{
                "A": "Option A",
                "B": "Option B",
                "C": "Option C",
                "D": "Option D"
            }},
            "answer": "A",
            "explanation": "Short explanation"
        }}
    ]
}}

Study material:

{text}
"""

            try:

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )

                response_text = response.text.strip()

                # Remove accidental markdown
                if response_text.startswith(
                    "```json"
                ):

                    response_text = (
                        response_text
                        .replace("```json", "")
                        .replace("```", "")
                        .strip()
                    )

                elif response_text.startswith("```"):

                    response_text = (
                        response_text
                        .replace("```", "")
                        .strip()
                    )

                quiz_data = json.loads(
                    response_text
                )

                questions = quiz_data["questions"]

                # Basic validation
                if not questions:

                    st.error(
                        "❌ No questions were generated."
                    )

                    st.stop()

                for question in questions:

                    required_keys = [
                        "question",
                        "options",
                        "answer",
                        "explanation"
                    ]

                    for key in required_keys:

                        if key not in question:

                            raise ValueError(
                                f"Missing field: {key}"
                            )

                    if question["answer"] not in [
                        "A", "B", "C", "D"
                    ]:

                        raise ValueError(
                            "Invalid answer option."
                        )

                # Save quiz
                st.session_state["quiz"] = questions

                st.session_state[
                    "quiz_submitted"
                ] = False

                st.session_state[
                    "difficulty"
                ] = difficulty

                st.session_state[
                    "time_limit"
                ] = time_limit

                st.success(
                    "🎉 Quiz generated successfully!"
                )

            except json.JSONDecodeError:

                st.error(
                    "❌ AI returned invalid JSON. "
                    "Please click Generate Quiz again."
                )

            except Exception as e:

                st.error(
                    f"❌ Error generating quiz: {e}"
                )


# =========================================================
# 9. DISPLAY QUIZ
# =========================================================

if st.session_state["quiz"] is not None:

    questions = st.session_state["quiz"]

    st.divider()

    st.header("📝 Your Quiz")

    st.info(
        f"🎯 Difficulty: "
        f"{st.session_state['difficulty']} | "
        f"⏱️ Time Limit: "
        f"{st.session_state['time_limit']} minutes"
    )


    # =====================================================
    # 10. QUESTIONS
    # =====================================================

    if not st.session_state["quiz_submitted"]:

        for i, question in enumerate(
            questions
        ):

            st.subheader(
                f"Question {i + 1}"
            )

            st.write(
                question["question"]
            )

            st.radio(
                "Select your answer:",
                options=["A", "B", "C", "D"],
                index=None,
                format_func=lambda option,
                q=question:
                    f"{option}. "
                    f"{q['options'][option]}",
                key=f"question_{i}"
            )


        # =================================================
        # 11. SUBMIT QUIZ
        # =================================================

        if st.button(
            "🏆 Submit Quiz",
            use_container_width=True
        ):

            score = 0

            for i, question in enumerate(
                questions
            ):

                user_answer = st.session_state.get(
                    f"question_{i}"
                )

                if user_answer == question["answer"]:

                    score += 1

            total = len(questions)

            percentage = (
                score / total
            ) * 100

            st.session_state["score"] = score

            st.session_state[
                "percentage"
            ] = percentage

            st.session_state[
                "quiz_submitted"
            ] = True

            st.rerun()


# =========================================================
# 12. RESULT DASHBOARD
# =========================================================

if (
    st.session_state["quiz"] is not None
    and st.session_state["quiz_submitted"]
):

    questions = st.session_state["quiz"]

    score = st.session_state["score"]

    percentage = st.session_state[
        "percentage"
    ]

    total = len(questions)


    # =====================================================
    # Calculate correct / wrong / unanswered
    # =====================================================

    correct = 0
    wrong = 0
    unanswered = 0

    for i, question in enumerate(
        questions
    ):

        user_answer = st.session_state.get(
            f"question_{i}"
        )

        if user_answer is None:

            unanswered += 1

        elif user_answer == question["answer"]:

            correct += 1

        else:

            wrong += 1


    # =====================================================
    # RESULT TITLE
    # =====================================================

    st.divider()

    st.header("🎯 Quiz Result")


    # =====================================================
    # SCORE CARDS
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "🏆 Score",
            f"{score}/{total}"
        )

    with col2:

        st.metric(
            "📊 Accuracy",
            f"{percentage:.0f}%"
        )

    with col3:

        st.metric(
            "✅ Correct",
            correct
        )

    with col4:

        st.metric(
            "❌ Wrong",
            wrong
        )


    # =====================================================
    # UNANSWERED
    # =====================================================

    st.metric(
        "⚪ Unanswered",
        unanswered
    )


    # =====================================================
    # PERFORMANCE MESSAGE
    # =====================================================

    if percentage == 100:

        st.balloons()

        st.success(
            "🏆 Perfect score! Excellent work!"
        )

    elif percentage >= 70:

        st.success(
            "🎉 Great job! You have a good understanding."
        )

    elif percentage >= 50:

        st.info(
            "👍 Good attempt! Keep practicing."
        )

    else:

        st.warning(
            "📚 Keep studying and try again!"
        )


    # =====================================================
    # PROGRESS BAR
    # =====================================================

    st.write("### 📈 Performance")

    st.progress(
        percentage / 100
    )


    # =====================================================
    # ANSWER REVIEW
    # =====================================================

    st.header("📖 Answer Review")

    for i, question in enumerate(
        questions
    ):

        st.write(
            f"### Question {i + 1}"
        )

        user_answer = st.session_state.get(
            f"question_{i}"
        )

        correct_answer = question["answer"]


        if user_answer is None:

            st.warning(
                "⚪ Not answered"
            )

            st.write(
                f"Correct answer: "
                f"**{correct_answer}**"
            )

        elif user_answer == correct_answer:

            st.success(
                f"✅ Correct! "
                f"Your answer: {user_answer}"
            )

        else:

            st.error(
                f"❌ Your answer: {user_answer} | "
                f"Correct answer: {correct_answer}"
            )


        st.write(
            f"**Explanation:** "
            f"{question['explanation']}"
        )


    # =====================================================
    # NEW QUIZ
    # =====================================================

    st.divider()

    if st.button(
        "🔄 Generate New Quiz",
        use_container_width=True
    ):

        st.session_state["quiz"] = None

        st.session_state[
            "quiz_submitted"
        ] = False

        st.session_state["score"] = 0

        st.session_state[
            "percentage"
        ] = 0

        st.rerun()