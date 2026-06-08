import os
from dotenv import load_dotenv
 
load_dotenv()

CHROMA_PATH = "./ChromaDB_LangFuse"
SQLITE_DB_PATH = "./SQL_DataBase.db"

AZURE = {
    "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
    "chat": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
    "embed": os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
}

LANGFUSE = {
    "public_key": os.getenv("LANGFUSE_PUBLIC_KEY"),
    "secret_key": os.getenv("LANGFUSE_SECRET_KEY") or os.getenv("LANGFUSE_PRIVATE_KEY"),
    "host":  os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"
}