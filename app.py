


import json
import re
import html
from pathlib import Path
import httpx
import streamlit as st
from google import genai
# =====================================================
# FAQgent AI — Customer Support Assistant
# =====================================================

st.set_page_config(
    page_title="FAQgent AI | Smart Customer Support",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).parent
@st.cache_resource
def get_gemini_client():
    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"],
        http_options={"timeout": 60000},
    )


# ------------------ DATA LOADING ---------------------

def load_json(filename):
    with (BASE_DIR / filename).open("r", encoding="utf-8") as file:
        return json.load(file)


try:
    faqs = load_json("faqs.json")
    orders = load_json("orders.json")
except (FileNotFoundError, json.JSONDecodeError):
    st.error(
        "The application could not load its data. "
        "Please check faqs.json and orders.json."
    )
    st.stop()


# ------------------ STYLING --------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --bg: #080b16;
        --panel: #101528;
        --panel-light: #151b31;
        --border: rgba(168, 177, 255, 0.15);
        --text: #f3f4ff;
        --muted: #9ba4c3;
        --violet: #9274ff;
        --cyan: #5eead4;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 12% 0%, rgba(91, 62, 190, .20), transparent 34%),
            radial-gradient(ellipse at 92% 18%, rgba(20, 184, 166, .09), transparent 30%),
            var(--bg);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stDecoration"] {
        display: none;
    }

    .block-container {
        max-width: 1050px;
        padding: 1.4rem 1.5rem 2.8rem;
    }

    /* Header */

    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 10px 0 24px;
        border-bottom: 1px solid var(--border);
        margin-bottom: 34px;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .brand-icon {
        width: 45px;
        height: 45px;
        display: grid;
        place-items: center;
        border-radius: 15px;
        color: white;
        font-size: 23px;
        background: linear-gradient(135deg, #8b5cf6, #5b5bd6 60%, #14b8a6);
        box-shadow: 0 8px 28px rgba(124, 92, 246, .30);
    }

    .brand-name {
        font: 800 23px 'Manrope', sans-serif;
        letter-spacing: -1px;
        color: #ffffff;
        margin: 0;
    }

    .brand-name span {
        color: #a99aff;
    }

    .brand-caption {
        font-size: 11px;
        color: var(--muted);
        margin: 2px 0 0;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border: 1px solid rgba(94, 234, 212, .20);
        border-radius: 999px;
        background: rgba(20, 184, 166, .08);
        color: #a5f3e7;
        font-size: 12px;
        white-space: nowrap;
    }

    .status-dot {
        height: 7px;
        width: 7px;
        border-radius: 50%;
        background: #5eead4;
        box-shadow: 0 0 12px #5eead4;
        animation: pulse 2s infinite;
    }

    /* Hero */

    .hero {
        text-align: center;
        padding: 12px 0 25px;
        animation: fadeUp .7s ease both;
    }

    .eyebrow {
        display: inline-block;
        padding: 7px 13px;
        border: 1px solid rgba(167, 139, 250, .25);
        border-radius: 999px;
        background: rgba(139, 92, 246, .09);
        color: #c4b5fd;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: .5px;
        margin-bottom: 20px;
    }

    .hero h1 {
        color: #ffffff;
        font: 800 clamp(30px, 5vw, 49px)/1.16 'Manrope', sans-serif;
        letter-spacing: -2px;
        margin: 0 auto 16px;
        max-width: 780px;
    }

    .gradient-text {
        background: linear-gradient(100deg, #b9a7ff, #7dd3fc, #5eead4);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }

    .hero-copy,
p.hero-copy {
    display: block !important;
    width: 100% !important;
    max-width: 600px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    text-align: center !important;
    color: #a4acc6;
    font-size: 15px;
    line-height: 1.8;
}
    /* Info strip */

    .feature-strip {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px;
        margin: 22px 0 28px;
    }

    .feature-chip {
        padding: 9px 13px;
        border: 1px solid var(--border);
        background: rgba(17, 23, 43, .75);
        border-radius: 10px;
        color: #c8cee3;
        font-size: 12px;
    }

    /* Chat panel */

    .section-label {
        color: #dce1f5;
        font: 700 15px 'Manrope', sans-serif;
        margin: 10px 0 6px;
    }

    .section-description {
        color: var(--muted);
        font-size: 12px;
        margin-bottom: 14px;
    }

    [data-testid="stChatMessage"] {
        background: rgba(17, 23, 43, .90);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 16px 18px;
        margin-bottom: 12px;
        animation: fadeUp .35s ease both;
    }

    /* User messages: right side */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    width: fit-content;
    max-width: 80%;
    margin-left: auto;
    margin-right: 0;
    flex-direction: row-reverse;
}

/* AI replies: left side */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    width: fit-content;
    max-width: 80%;
    margin-left: 0;
    margin-right: auto;
}
    

    [data-testid="stChatMessage"] p {
        color: #e5e9fa;
        line-height: 1.75;
    }

    [data-testid="stChatMessageAvatarUser"] {
        background: #6554d9;
    }

    [data-testid="stChatMessageAvatarAssistant"] {
        background: #0f766e;
    }

    [data-testid="stChatInput"] {
        border: 1px solid rgba(167, 139, 250, .35);
        border-radius: 17px;
        background: #11172b;
        box-shadow: 0 0 0 1px rgba(139, 92, 246, .04);
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: #9274ff;
        box-shadow: 0 0 22px rgba(139, 92, 246, .13);
    }

    [data-testid="stChatInput"] textarea {
        color: white;
        font-size: 14px;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #7e87a6;
    }

    /* Suggestion buttons */

    div.stButton > button {
        border: 1px solid rgba(168, 177, 255, .16);
        background: rgba(17, 23, 43, .80);
        color: #dfe4fa;
        border-radius: 13px;
        min-height: 48px;
        transition: all .22s ease;
        font-size: 13px;
    }

    div.stButton > button:hover {
        border-color: #8b78ee;
        background: rgba(111, 82, 205, .18);
        color: #ffffff;
        transform: translateY(-2px);
    }

    div.stButton > button:focus {
        box-shadow: 0 0 0 2px rgba(139, 92, 246, .35);
    }

    /* Footer */

    .trust-note {
        border: 1px solid var(--border);
        border-radius: 13px;
        padding: 13px 15px;
        color: #9ca7c6;
        background: rgba(16, 21, 40, .65);
        font-size: 12px;
        line-height: 1.7;
        margin-top: 22px;
    }

    .footer {
        text-align: center;
        color: #68728f;
        font-size: 11px;
        padding: 25px 0 4px;
    }

    /* Animations */

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: .55; transform: scale(.82); }
    }

    @media (max-width: 640px) {
        .block-container {
            padding: 1rem .85rem 2rem;
        }

        .topbar {
            margin-bottom: 24px;
        }

        .brand-name {
            font-size: 20px;
        }

        .hero h1 {
            letter-spacing: -1.3px;
        }

        .hero-copy {
            font-size: 13px;
        }

        .feature-strip {
            gap: 7px;
        }

        [data-testid="stChatMessage"] {
            padding: 12px;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: .01ms !important;
            transition-duration: .01ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ------------------ AGENT TOOLS ---------------------

def find_order(order_id):
    for order in orders:
        if order["order_id"].upper() == order_id.upper():
            return order
    return None


def search_faq(question):
    normalized = question.lower()
    question_words = set(re.findall(r"\b[a-z0-9]+\b", normalized))

    best_faq = None
    best_score = 0

    for faq in faqs:
        candidates = [faq["question"]] + faq.get("keywords", [])
        score = 0

        for candidate in candidates:
            candidate = candidate.lower()
            candidate_words = set(
                re.findall(r"\b[a-z0-9]+\b", candidate)
            )

            if candidate in normalized:
                score = max(score, len(candidate_words) + 1)
            else:
                score = max(
                    score,
                    len(question_words & candidate_words),
                )

        if score > best_score:
            best_score = score
            best_faq = faq

    # Require a meaningful match instead of guessing.
    if best_score >= 1:
        return best_faq

    return None




def run_agent(user_message):
    message = user_message.strip()

    if not message:
        return "Please enter a question so I can help."

    # 1. Handle order tracking locally
    order_match = re.search(r"\bORD\d+\b", message, re.IGNORECASE)

    order_keywords = [
        "order status",
        "track order",
        "track my order",
        "where is my order",
        "check order",
        "order update",
    ]

    if order_match:
        order_id = order_match.group(0).upper()
        order = find_order(order_id)

        if not order:
            return (
                f"I couldn't find **{order_id}** in the sample records. "
                "Please check the ID and try again."
            )

        items = ", ".join(order["items"])

        return (
            "### Your order details\n\n"
            f"**Order ID:** {order['order_id']}\n\n"
            f"**Status:** {order['status']}\n\n"
            f"**Items:** {items}\n\n"
            f"**Estimated delivery:** "
            f"{order['estimated_delivery']}\n\n"
            "_This is a fictional order record for demonstration._"
        )

    if any(keyword in message.lower() for keyword in order_keywords):
        return (
            "I can check an order in our demo records. "
            "Please include its ID, such as **ORD101**."
        )

    # 2. Load the actual FAQ data
    try:
        faq_path = Path(__file__).with_name("faqs.json")

        with open(faq_path, "r", encoding="utf-8") as file:
            faqs = json.load(file)

    except (OSError, json.JSONDecodeError):
        st.error("The FAQ data could not be loaded.")
        return (
            "I'm having trouble accessing the FAQ information. "
            "Please try again later."
        )

    # 3. Prepare recent conversation history
    history = st.session_state.get("messages", [])
    contents = []

    for item in history:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        text = item.get("content", "")

        if not isinstance(text, str) or not text.strip():
            continue

        # Gemini uses "model" instead of "assistant"
        if role == "assistant":
            role = "model"

        if role not in ("user", "model"):
            continue

        # Avoid sending the current question twice if
        # it has already been added to Streamlit history.
        if role == "user" and text.strip() == message:
            continue

        contents.append({
            "role": role,
            "parts": [{"text": text}]
        })

    # Keep only recent messages to limit API usage.
    contents = contents[-8:]

    # Add the current question last.
    contents.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    # 4. Ask Gemini using the FAQ data and conversation
    try:
        api_key = st.secrets["GEMINI_API_KEY"]

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-flash-lite-latest:generateContent"
        )

        response = httpx.post(
            url,
            headers={"x-goog-api-key": api_key},
            json={
                "system_instruction": {
                    "parts": [{
                        "text": (
                            "You are FAQgent-AI, a helpful food-delivery "
                            "customer support assistant for a college demo.\n\n"
                            "Use the FAQ records below as the source of truth "
                            "for service policies and support answers. "
                            "Answer in simple, friendly language.\n"
                            "Do not invent policies, refund timelines, "
                            "order details, or features that are not provided.\n"
                            "If the FAQs do not contain the answer, say so "
                            "and suggest checking the Help section.\n"
                            "Use recent conversation history to understand "
                            "follow-up questions, but do not treat earlier "
                            "assistant answers as official policy.\n"
                            "This is a fictional demonstration, not a real "
                            "food-delivery service.\n\n"
                            "FAQ DATA:\n"
                            + json.dumps(faqs, ensure_ascii=False)
                        )
                    }]
                },
                "contents": contents,
                "generationConfig": {
                    "maxOutputTokens": 500
                }
            },
            timeout=20.0,
        )

        # 5. Handle API errors
        if response.status_code == 429:
            return (
                "I'm receiving too many requests right now. "
                "Please wait a little and try again."
            )

        if response.status_code in (401, 403):
            st.error(
                f"Gemini API access error: HTTP {response.status_code}"
            )
            return (
                "The AI service could not authorize this request. "
                "Please check the API configuration."
            )

        if response.status_code >= 500:
            return (
                "The AI service is temporarily unavailable. "
                "Please try again shortly."
            )

        if not response.is_success:
            st.error(
                f"Gemini API returned HTTP {response.status_code}."
            )
            return (
                "I couldn't process that question. "
                "Please try rephrasing it."
            )

        data = response.json()

        candidates = data.get("candidates", [])

        if not candidates:
            return (
                "I couldn't generate an answer this time. "
                "Please try asking another way."
            )

        parts = candidates[0].get("content", {}).get("parts", [])

        answer = "\n".join(
            part["text"]
            for part in parts
            if isinstance(part.get("text"), str)
        ).strip()

        return answer or (
            "I couldn't generate an answer this time. "
            "Please try again."
        )

    except httpx.TimeoutException:
        return (
            "The AI is taking longer than expected. "
            "Please try again in a moment."
        )

    except httpx.RequestError:
        return (
            "I couldn't reach the AI service. "
            "Please check your internet connection and try again."
        )

    except Exception as e:
        st.error(f"Unexpected error: {type(e).__name__}")
        return (
            "Something went wrong while processing your question. "
            "Please try again."
        )




# ------------------ SESSION STATE -------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None


# ------------------ HEADER ---------------------------

st.markdown(
    """
    <div class="topbar">
        <div class="brand">
            <div class="brand-icon">FA⬡</div>
            <div>
                <p class="brand-name">FAQ<span>gent</span> AI</p>
                <p class="brand-caption">CUSTOMER SUPPORT ASSISTANT
FOR FOOD DELIVERY</p>
            </div>
        </div>
        <div class="status-pill">
            <span class="brand-icon">⬡</span>
            Assistant ready
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------ HERO -----------------------------

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">✧ SMARTER SUPPORT, SIMPLIFIED</div>
        <h1>
            Good questions deserve<br>
            <span class="gradient-text">helpful answers.</span>
        </h1>
        <p class="hero-copy">
            Your food-delivery support companion. Get help with
            orders, payments, refunds, and delivery questions —
            all in one conversation.
        </p>
    </div>

    <div class="feature-strip">
        <div class="feature-chip">⬡ FAQ assistance</div>
        <div class="feature-chip">↗ Sample order lookup</div>
        <div class="feature-chip">◈ Clear responses</div>
        <div class="feature-chip">✓ Available anytime</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ------------------ CHAT HISTORY ---------------------

st.markdown(
    '<div class="section-label">Your conversation</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-description">'
    'Ask naturally. FAQgent will look for a relevant answer.'
    '</div>',
    unsafe_allow_html=True,
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ------------------ SUGGESTIONS ----------------------

if not st.session_state.messages:
    st.markdown(
        '<div class="section-label">What can I help you with?</div>',
        unsafe_allow_html=True,
    )

    suggestions = [
        ("↩  Refunds & payments", "How can I get a refund?"),
        ("📦  Track an order", "Check order ORD101"),
        ("🛵  Delivery issues", "Why is my order delayed?"),
        ("✕  Cancel an order", "How can I cancel my order?"),
    ]

    col1, col2 = st.columns(2)

    for index, (label, question) in enumerate(suggestions):
        with (col1 if index % 2 == 0 else col2):
            if st.button(label, key=f"suggestion_{index}", use_container_width=True):
                st.session_state.pending_question = question
                st.rerun()


# ------------------ CHAT INPUT -----------------------

typed_question = st.chat_input(
    "Message FAQgent... Ask about an order, refund, or delivery"
)

question = typed_question

if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None

if question and question.strip():
    st.session_state.messages.append(
        {"role": "user", "content": question.strip()}
    )

    answer = run_agent(question)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

    st.rerun()


# ------------------ FOOTER ACTIONS -------------------

st.divider()

left, right = st.columns([4, 1])

with left:
    st.markdown(
        '<div class="trust-note">'
        '🔐 <b>Demo environment</b><br>'
        'FAQent uses sample FAQ content and fictional order records. '
        'It does not access real customer accounts, payments, '
        'or live delivery systems.'
        '</div>',
        unsafe_allow_html=True,
    )

with right:
    st.write("")
    st.write("")
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_question = None
        st.rerun()

st.markdown(
    '<div class="footer">'
    'FAQgent AI · Intelligent Customer Support · College Mini Project'
    '</div>',
    unsafe_allow_html=True,
)

