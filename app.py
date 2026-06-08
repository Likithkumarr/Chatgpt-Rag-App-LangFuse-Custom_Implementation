import streamlit as st
import re
import json
from utils.session import init_session
from auth.login import login
from auth.register import register
from chat.chat_engine import get_llms
from chat.chat_ui import render_sidebar
from chat.history import get_history
from feedback.rlhf import handle_feedback
from db import save_session, save_chat_message
from config import AZURE

# NEW: Langfuse imports
from utils.langfuse_utils import create_trace, add_score, langfuse_client, log_generation

init_session()

# AUTH
st.set_page_config(page_title="ChatBot with RAG and RLHF", page_icon="🤖", layout="wide")
if not st.session_state.logged_in:
    st.title("🔐 Multi-User Secure Chat")
    st.info("Don't have an account? Go to **Register**. Already have an account? Go to **Login**.")
    tab1, tab2 = st.tabs(["Login", "Register"])
 
    with tab1:
        login()
 
    with tab2:
        register()

else:
    current_name = st.session_state.display_name or st.session_state.username
    st.title(f"🤖 Welcome {current_name}")
    # ---------- SIDEBAR ----------
    render_sidebar()
    # LLM
    llm1, llm2 = get_llms()
    # Messages
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])
 
    prompt = st.chat_input("Message...")
    
    if prompt or st.session_state.retry_trigger:
        if st.session_state.retry_trigger:
            user_query = st.session_state.messages[-1]["content"] 
            bad_answer = st.session_state.messages[-1]["content"]
            st.warning("🔄 Generating a fresh, different response...")
            active_llm = llm2  
            instruction = f"""
            The user disliked your previous response. 
            PREVIOUS RESPONSE: {bad_answer}
            
            Provide a DIFFERENT perspective or more detail. 
            Do NOT repeat the same explanation or phrasing.
            """
        else:
            user_query = prompt
            active_llm = llm1
            instruction = "Be concise and helpful."
            name_match = re.search(r"(?:my name is|i am) (\w+)", user_query.lower())
            if name_match: st.session_state.display_name = name_match.group(1).capitalize()
            
            st.session_state.messages.append({"role": "user", "content": user_query})
            save_chat_message(
                st.session_state.current_session_id,
                st.session_state.username,
                "user",
                user_query,
            )
            with st.chat_message("user"): st.markdown(user_query)

        interaction_type = "retry" if st.session_state.retry_trigger else "standard"
        
        # 1. Use start_as_current_span (confirmed available in your environment)
        with langfuse_client.start_as_current_span(
            name="chat_interaction" if not st.session_state.retry_trigger else "chat_retry"
        ) as span:
            trace_id = langfuse_client.get_current_trace_id() or "fallback_id"
            st.session_state.last_trace_id = trace_id
            langfuse_client.update_current_trace(
                user_id=st.session_state.username,
                session_id=st.session_state.current_session_id,
                input=user_query
            )
            # Flush immediately to make the trace row appear in the dashboard instantly
            langfuse_client.flush()
            
            with st.chat_message("assistant"):
                all_past_interactions = get_history(st.session_state.username)
                doc_context = ""
                response = ""
                usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                
                # Check if user is asking "What did I upload?"
                if "UPLOAD" in user_query.upper() and ("WHAT" in user_query.upper() or "NAME" in user_query.upper()):
                    filenames = st.session_state.get('uploaded_filenames', [])
                    if filenames:
                        response = f"You have uploaded the following documents: {', '.join(filenames)}"
                        st.info("📄 Using document metadata")
                    else:
                        response = "You haven't uploaded any documents in this session yet."
                        st.info("🤖 General AI response")
                    used_doc_final = True
                else:
                    used_doc_final = False

                if not used_doc_final and st.session_state.retriever:
                    docs = st.session_state.retriever.invoke(user_query)
                    doc_context = ""
                    use_doc = False

                    if docs and len(docs) > 0:
                        doc_context = "\n".join([d.page_content for d in docs])
                        keyword_match = any(user_query.lower() in d.page_content.lower() for d in docs)
                        
                        if keyword_match or len(doc_context) > 100:
                            use_doc = True

                    # --- STEP 1: TRY DOCUMENT RETRIEVAL ---
                    if use_doc:
                        doc_prompt = f"""
                            You are strict Document QA System.
                            Context: {doc_context}
                            Question: {user_query}
                            Rules: Answer ONLY from context. If not found, say 'I don't know'.
                        """
                        try:
                            res = active_llm.invoke(doc_prompt)
                            usage = res.response_metadata.get("token_usage", usage)
                            if "I DON'T KNOW" not in res.content.upper() and "NOT CONTAIN" not in res.content.upper():
                                used_doc_final = True
                                response = res.content
                                st.info("📄 Using document")
                        except Exception as e:
                            if "content_filter" in str(e):
                                st.warning("⚠️ The retrieved document segments triggered Azure's safety filter. Falling back to general knowledge.")
                                used_doc_final = False
                            else:
                                st.error(f"LLM Error: {e}")
                                st.stop()

                # --- STEP 2: FALLBACK TO GENERAL AI ---
                if not response:
                    ai_prompt = f"""{instruction}
                        You are a helpful assistant.
                        User name: {current_name}
                        Memory: {all_past_interactions}
                        Question: {user_query}
                    """
                    with st.spinner("🤔 Thinking..."):
                        res = active_llm.invoke(ai_prompt)
                        response = res.content
                        usage = res.response_metadata.get("token_usage", usage)
                    st.info("🤖 General AI response")

                st.markdown(response)

            # Save assistant message
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response,
                "trace_id": trace_id
            })
            save_chat_message(
                st.session_state.current_session_id,
                st.session_state.username,
                "assistant",
                response,
            )

            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # Example Pricing (e.g. GPT-3.5-Turbo): $0.0015 / 1k input, $0.002 / 1k output
            input_cost = (prompt_tokens / 1000) * 0.0015
            output_cost = (completion_tokens / 1000) * 0.002
            total_cost = input_cost + output_cost

            # 2. Add Observation and detailed Usage/Cost metrics
            log_generation(
                trace_id=trace_id,
                name="llm-generation",
                input_text=user_query,
                output_text=response,
                usage=usage,
                model=AZURE.get("chat", "azure-openai")
            )

            # 3. Tracking metrics as scores for dashboard analytics
            add_score(trace_id, "input-tokens", prompt_tokens)
            add_score(trace_id, "output-tokens", completion_tokens)
            add_score(trace_id, "total-tokens", total_tokens)
            add_score(trace_id, "total-cost", total_cost)

            # 4. Finalize the trace with output and remaining metadata
            langfuse_client.update_current_trace(
                output=response,
                metadata={
                    "interaction_type": interaction_type,
                    "usage": usage
                },
                tags=[interaction_type, "production"]
            )

        # Ensure tags and trace updates are sent before rerun
        langfuse_client.flush()

        # Save session metadata
        session_title = None
        if st.session_state.messages:
            first_user = next((m for m in st.session_state.messages if m["role"] == "user"), None)
            if first_user:
                session_title = first_user["content"][:40]

        save_session(
            st.session_state.current_session_id,
            st.session_state.username,
            json.dumps(st.session_state.messages),
            title=session_title,
        )
        st.session_state.retry_trigger = False
        st.rerun()
    # ---------- RLHF ----------
    handle_feedback(st)