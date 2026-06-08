import os
from dotenv import load_dotenv

load_dotenv()  # make sure this is called before accessing env vars

print("Public key:", os.getenv("LANGFUSE_PUBLIC_KEY"))
print("Private key:", os.getenv("LANGFUSE_SECRET_KEY"))
print("Host:", os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST") or "https://cloud.langfuse.com")

from langfuse import Langfuse
lf=Langfuse(public_key=os.getenv("LANGFUSE_PUBLIC_KEY"), secret_key=os.getenv("LANGFUSE_SECRET_KEY"), host=os.getenv("LANGFUSE_BASE_URL") or os.getenv("LANGFUSE_HOST") or "https://cloud.langfuse.com")
print(dir(lf))
print("Connection Successful:", lf.auth_check())
print("hello world ")