from langfuse import Langfuse
from config import LANGFUSE

langfuse_client = Langfuse(
    public_key=LANGFUSE["public_key"],
    secret_key=LANGFUSE["secret_key"],
    host=LANGFUSE["host"],
    # Settings for immediate data delivery
    flush_at=1, 
    flush_interval=0.5, # Small interval to keep the worker active
    # Optional: helps with debugging connection issues
    debug=False 
)

def create_trace(name, user_id, input_text, output_text, session_id=None, metadata=None, tags=None):
    """Creates a trace and returns the trace_id."""
    with langfuse_client.start_as_current_span(name=name) as span:
        langfuse_client.update_current_trace(
            user_id=user_id,
            session_id=session_id,
            input=input_text,
            output=output_text,
            metadata=metadata,
            tags=tags or ["production"]
        )
        return langfuse_client.get_current_trace_id()

def add_score(trace_id, score_name, value, comment=None):
    """Adds a score to an existing trace using its ID."""
    langfuse_client.create_score(
        trace_id=trace_id,
        name=score_name,
        value=float(value),
        comment=comment,
    )

def log_generation(trace_id, name, input_text, output_text, usage, model=None, metadata=None):
    """Creates a generation observation linked to a specific trace."""
    if metadata is None:
        metadata = {}
    
    with langfuse_client.start_as_current_generation(
        name=name,
        input=input_text,
        model=model,
        metadata=metadata
    ) as generation:
        # Update using the returned generation object to bypass signature issues in the client helper.
        # We also map Azure OpenAI usage keys to Langfuse expected keys (input/output/total).
        generation.update(
            output=output_text,
            metadata=metadata,
            usage={
                "input": usage.get("prompt_tokens", 0),
                "output": usage.get("completion_tokens", 0),
                "total": usage.get("total_tokens", 0)
            }
        )

def get_trace_url(trace_id):
    return langfuse_client.get_trace_url()
