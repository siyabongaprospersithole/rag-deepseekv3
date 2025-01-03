import streamlit as st
import requests
import json
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="PDF Chat Assistant",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stAlert {
        padding: 0.5rem;
        margin: 1rem 0;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e6f3ff;
        border-left: 5px solid #2e6da4;
        color: black;
    }
    .assistant-message {
        background-color: #f0f2f6;
        border-left: 5px solid #4CAF50;
        color:black;
    }
    .message-header {
        color: #666;
        font-size: 0.8rem;
        margin-bottom: 0.5rem;
    }
    .pdf-preview {
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'pdf_uploaded' not in st.session_state:
    st.session_state.pdf_uploaded = False
if 'pdf_name' not in st.session_state:
    st.session_state.pdf_name = None
if 'pdf_preview' not in st.session_state:
    st.session_state.pdf_preview = None

# Title and description
st.title("📚 PDF Chat Assistant")
st.markdown("Upload a PDF and ask questions about its content.")

# Sidebar
with st.sidebar:
    st.header("📋 Document Info")
    if st.session_state.pdf_name:
        st.success(f"Current PDF: {st.session_state.pdf_name}")
        if st.session_state.pdf_preview:
            with st.expander("Document Preview"):
                st.markdown(f"```\n{st.session_state.pdf_preview}\n```")
    else:
        st.info("No PDF uploaded yet")
    
    st.header("🔧 Settings")
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()
    
    st.header("ℹ️ How to use")
    st.markdown("""
    1. Upload a PDF file
    2. Click 'Process PDF' to analyze
    3. Type your question
    4. Click 'Ask' or press Enter
    
    **Tips:**
    - Ask specific questions
    - Questions about document content work best
    - Use clear and concise language
    """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # File upload section
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])

    if uploaded_file is not None:
        if st.button("Process PDF", key="process_pdf"):
            with st.spinner('Processing PDF...'):
                try:
                    files = {'pdf': uploaded_file}
                    response = requests.post('http://localhost:5000/api/upload', files=files)
                    
                    if response.status_code == 200:
                        st.session_state.pdf_uploaded = True
                        st.session_state.pdf_name = uploaded_file.name
                        st.session_state.pdf_preview = response.json().get('preview', '')
                        st.success("PDF processed successfully!")
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error connecting to server: {str(e)}")

with col2:
    # Question input
    question = st.text_input("Ask a question about the PDF:", key="question_input")
    
    if st.button("Ask", key="ask_button") and question:
        if not st.session_state.pdf_uploaded:
            st.error("Please upload and process a PDF first.")
        else:
            with st.spinner('Getting answer...'):
                try:
                    response = requests.post(
                        'http://localhost:5000/api/ask',
                        json={'question': question},
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code == 200:
                        answer = response.json().get('answer', '')
                        # Add to chat history
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        st.session_state.chat_history.append({
                            'type': 'user',
                            'content': question,
                            'timestamp': timestamp
                        })
                        st.session_state.chat_history.append({
                            'type': 'assistant',
                            'content': answer,
                            'timestamp': timestamp
                        })
                        # Clear question input
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error connecting to server: {str(e)}")

# Display chat history
st.header("💬 Chat History")
if not st.session_state.chat_history:
    st.info("No messages yet. Upload a PDF and ask questions to get started!")
else:
    for message in st.session_state.chat_history:
        message_type = message['type']
        is_user = message_type == 'user'
        
        with st.container():
            st.markdown(
                f"""
                <div class="chat-message {'user-message' if is_user else 'assistant-message'}">
                    <div class="message-header">
                        {'You' if is_user else 'Assistant'} - {message['timestamp']}
                    </div>
                    {message['content']}
                </div>
                """,
                unsafe_allow_html=True
            ) 