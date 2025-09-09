from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from pathlib import Path

KB_PATH = Path("knowledge/faq")
FAISS_PATH = Path("faiss_index")

class RAGModule:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        if FAISS_PATH.exists():
            self.db = FAISS.load_local(str(FAISS_PATH), self.embeddings, allow_dangerous_deserialization=True)
        else:
            self._build_index()

    def _build_index(self):
        docs = []
        for file in KB_PATH.glob("*"):
            text = file.read_text(encoding="utf-8")
            docs.append(Document(page_content=text, metadata={"source": file.name}))
        self.db = FAISS.from_documents(docs, self.embeddings)
        self.db.save_local(str(FAISS_PATH))

    def ask(self, question: str) -> str:
        docs = self.db.similarity_search(question, k=2)
        context = "\n\n".join([d.page_content for d in docs])
        return f"📚 Ответ:\n{context[:1000]}...\n\n📎 Источник: {docs[0].metadata['source']}"
