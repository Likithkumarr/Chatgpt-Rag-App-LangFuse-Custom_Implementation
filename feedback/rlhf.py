import uuid
import streamlit as st
from db import get_last_chat_message, update_chat_message_feedback, save_feedback
from utils.langfuse_utils import add_score, langfuse_client

def save_feedback_entry(session_id, messages, feedback):
    message = get_last_chat_message(session_id, role="assistant")
    if not message:
        return

    update_chat_message_feedback(message["id"], feedback)

    prompt_text = ""
    if len(messages) >= 2 and messages[-2].get("role") == "user":
        prompt_text = messages[-2].get("content", "")

    # Save locally in your DB
    save_feedback(
        str(uuid.uuid4()),
        message["username"],
        session_id,
        prompt_text,
        message["content"],
        feedback,
    )

    # Send feedback to Langfuse linked to the specific trace
    message_data = messages[-1] if messages else {}
    trace_id = message_data.get("trace_id") or st.session_state.get("last_trace_id")

    if trace_id:
        # Explicitly map "good" to 1 and "bad" to 0 as requested
        score_value = 1.0 if feedback == "good" else 0.0
        add_score(
            trace_id=trace_id,
            score_name="user-feedback",
            value=score_value,
            comment=f"User marked response as {feedback}"
        )
        # Explicitly flush feedback as it's a standalone event
        langfuse_client.flush()

def handle_feedback(st):
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        c1, c2 = st.columns([1, 8])

        with c1:
            if st.button("👍"):
                save_feedback_entry(
                    st.session_state.current_session_id,
                    st.session_state.messages,
                    "good",
                )
                st.success("Saved as good feedback")

        with c2:
            if st.button("👎"):
                save_feedback_entry(
                    st.session_state.current_session_id,
                    st.session_state.messages,
                    "bad",
                )
                st.session_state.messages.pop()
                st.session_state.retry_trigger = True
                st.rerun()
