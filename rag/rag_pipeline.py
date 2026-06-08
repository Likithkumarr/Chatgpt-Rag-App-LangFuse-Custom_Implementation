import time, os
import openai
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from config import AZURE, CHROMA_PATH
import streamlit as st
from rag.file_loader import load_files
 
@retry(wait=wait_random_exponential(min=2, max=60),
       stop=stop_after_attempt(10),
       retry=retry_if_exception_type(openai.RateLimitError))
def add_batch(vstore, batch):
    vstore.add_documents(batch)
 
def build_rag(uploaded_files):
    if not uploaded_files:
        return None
    documents=load_files(uploaded_files)
    if not documents:
        return None
    # Now split the newly created 'all_documents' list
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
 
    emb = AzureOpenAIEmbeddings(
        azure_endpoint=AZURE["endpoint"],
        api_key=AZURE["api_key"],
        api_version=AZURE["api_version"],
        azure_deployment=AZURE["embed"],
        chunk_size=10
    )
 
    vectorstore = Chroma(persist_directory=CHROMA_PATH, embedding_function=emb)
 
    progress = st.progress(0)
    status = st.empty()
 
    batch_size = 20
    total = len(chunks)
 
    for i in range(0, total, batch_size):
        batch = chunks[i:i+batch_size]
 
        status.text(f"Processing {i} → {i+len(batch)} / {total}")
        add_batch(vectorstore, batch)
 
        progress.progress(min((i+batch_size)/total,1))
        time.sleep(2)
 
    status.text("✅ Done")
    time.sleep(1)
    progress.empty()
    status.empty()
 
    return vectorstore.as_retriever()