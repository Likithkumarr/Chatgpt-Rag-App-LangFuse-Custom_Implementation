import streamlit as st
import uuid
 
def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.update({
            "logged_in": False,
            "username": None,
            "display_name": None,
            "messages": [],
            "current_session_id": str(uuid.uuid4()),
            "retriever": None,
            "retry_trigger": False,
            "uploaded_filenames": []
        })
