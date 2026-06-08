import streamlit as st
import json
import uuid
from db import get_user_sessions, delete_user_sessions, get_session_messages
import time
from rag.rag_pipeline import build_rag

def render_sidebar():
 
    with st.sidebar:
        st.subheader(f"👤 {st.session_state.username}")
 
        # ---------------- CONTROL BUTTONS ----------------
        if st.button("➕ New Chat Session"):
            st.session_state.current_session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
 
        if st.button("🧹 Clear Current Screen"):
            st.session_state.messages = []
            st.rerun()
 
        if st.button("🗑️ DELETE ALL MY HISTORY"):
            delete_user_sessions(st.session_state.username)
            st.session_state.messages = []
            st.session_state.current_session_id = str(uuid.uuid4())
            st.warning("All history deleted forever!")
            st.rerun()
 
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()
 
        st.divider()
        # ---------------- FILE UPLOAD ----------------
        uploaded_files = st.file_uploader(
            "Upload Knowledge Files",
            accept_multiple_files=True
        )
        if uploaded_files:
            st.session_state.uploaded_filenames = [f.name for f in uploaded_files]
    
            if uploaded_files and not st.session_state.retriever:
                with st.status("🚀 Initializing Document Engine...", expanded=True) as s:
                    st.session_state.retriever = build_rag(uploaded_files)
                    st.write("📂 Reading uploaded files...")
                    # Simulate your file processing
                    time.sleep(1)

                    st.write("✂️ Splitting text into chunks...")
                    time.sleep(1)

                    st.write("🧠 Generating vector embeddings (Azure OpenAI)...")
                    time.sleep(1)

                    st.write("✅ Database persistence complete.")
                    s.update(label="✨ Indexing Complete!", state="complete",expanded=False)
        st.divider()
 
        # ---------------- CHAT HISTORY ----------------
        st.subheader("📜 Your Past Chats")
 
        user_chats = get_user_sessions(st.session_state.username)
 
        for session in user_chats:
            messages = get_session_messages(session["session_id"])
            message_count = len(messages)
            good_count = sum(1 for m in messages if m["feedback"] == "good")
            bad_count = sum(1 for m in messages if m["feedback"] == "bad")
            title = session["title"] or session["session_id"][:8]
            label = f"💬 {title[:15]} ({session['session_id'][:8]}) [{message_count} msgs | 👍 {good_count} | 👎 {bad_count}]"
 
            if st.button(label, key=f"h_{session['session_id']}"):
                st.session_state.current_session_id = session["session_id"]
                try:
                    st.session_state.messages = json.loads(session["document"]) or []
                except Exception:
                    st.session_state.messages = []
                st.rerun()

        return uploaded_files