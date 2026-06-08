import json
from db import get_user_sessions, get_session_messages
 
def get_history(username):
    sessions = get_user_sessions(username)
    history = []

    for session in sessions:
        history.append(f"--- Session {session['session_id']} ({session['updated_at']}) ---")
        msgs = get_session_messages(session['session_id'])
        for m in msgs:
            role = "User" if m["role"] == "user" else "Assistant"
            feedback = ""
            if m["role"] == "assistant" and m["feedback"]:
                feedback = f" [{m['feedback'].upper()}]"
            history.append(f"[{session['session_id'][:8]}] {role}: {m['content']}{feedback}")
 
    return "\n".join(history[-60:])

# def get_history(username):
#     data = chat_coll.get(where={"username": username})
#     questions = []
 
#     if data and data.get("documents"):
#         for doc in data["documents"]:
#             try:
#                 msgs = json.loads(doc)
#                 for m in msgs:
#                     if m.get("role") == "user":
#                         questions.append(m.get("content", ""))
#             except:
#                 continue
#     last 20 Questions
#     questions=questions[-20:]
#     return "\n".join(history)
#     return "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])


# def get_history(username):
#     data = chat_coll.get(where={"username": username})
#     history = []
 
#     if data and data.get("documents"):
#         for doc in data["documents"]:
#             try:
#                 msgs = json.loads(doc)
 
#                 i = 0
#                 while i < len(msgs):
#                     if msgs[i].get("role") == "user":
#                         question = msgs[i].get("content", "")
 
#                         # check if next message is assistant
#                         if i + 1 < len(msgs) and msgs[i+1].get("role") == "assistant":
#                             answer = msgs[i+1].get("content", "")
#                         else:
#                             answer = "No answer available"
 
#                         history.append((question, answer))
#                         i += 2  # move to next pair
#                     else:
#                         i += 1
 
#             except:
#                 continue
 
#     # format output
#     output = []
#     for idx, (q, a) in enumerate(history, 1):
#         output.append(f"{idx}. Q: {q}\n   A: {a}")
 
#     return "\n\n".join(output)