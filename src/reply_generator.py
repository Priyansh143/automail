import yaml
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
import os



# 1. Load Profile
def load_profile(path="config/profile.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f)


# 2. Convert profile dict → text chunks for embedding
def profile_to_chunks(profile_dict):
    text = yaml.dump(profile_dict, default_flow_style=False)  # YAML to string
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)
    return [Document(page_content=chunk) for chunk in chunks]


# 3. Build FAISS vectorstore
def load_or_create_vectorstore(docs, persist_dir="vectorstore"):
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")  # local embedding model

    if os.path.exists(persist_dir):
        print(f"📂 Loading existing vectorstore from {persist_dir}")
        return FAISS.load_local(persist_dir, embeddings, allow_dangerous_deserialization=True)

    print("📦 Building new vectorstore...")
    vectorstore = FAISS.from_documents(docs, embeddings)
    vectorstore.save_local(persist_dir)
    return vectorstore


# 4. Retrieve relevant profile info
def retrieve_profile_info(vectorstore, query, k=3):
    return vectorstore.similarity_search(query, k=k)


# 5. Generate reply
def generate_reply(email_body, sender, llm, vectorstore):
    retrieved_docs = retrieve_profile_info(vectorstore, email_body)
    retrieved_text = "\n".join([doc.page_content for doc in retrieved_docs])

    prompt_template = PromptTemplate(
        input_variables=["sender", "email_body", "retrieved_text"],
        template=(
            "You are Priyansh Kashyap. Use the following background info to write a professional reply.\n\n"
            "Relevant Profile Info:\n{retrieved_text}\n\n"
            "From: {sender}\n"
            "Message: {email_body}\n\n"
            "Reply:\n"
        )
    )

    prompt = prompt_template.format(
        sender=sender,
        email_body=email_body,
        retrieved_text=retrieved_text
    )

    return llm.invoke(prompt).strip()


# ===== MAIN TEST =====
if __name__ == "__main__":
    profile = load_profile()
    docs = profile_to_chunks(profile)
    vectorstore = load_or_create_vectorstore(docs)
    llm = Ollama(model="gemma3:4b")

    sample_email = "Hi Priyansh, we are looking for someone skilled in LangChain and RAG systems for an upcoming AI project."
    sender = "Alex from TechNova"

    reply = generate_reply(sample_email, sender, llm, vectorstore)
    print("\n📧 Auto-Reply:\n", reply)
