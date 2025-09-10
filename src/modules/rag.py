# src/modules/rag.py
import os
from pathlib import Path
from typing import List, Dict, Optional

from langchain_community.vectorstores import FAISS
from langchain_community.docstore.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastembed import TextEmbedding

from ..chains import rag_answer  # путь может отличаться в вашем проекте

KB_PATH    = Path(os.getenv("KB_DIR", "knowledge/faq")).resolve()
FAISS_PATH = Path(os.getenv("FAISS_DIR", "faiss_index")).resolve()
CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", "800"))
CH_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "120"))
EMB_MODEL  = os.getenv("EMB_MODEL", "BAAI/bge-small-en-v1.5")

KB_PATH.mkdir(parents=True, exist_ok=True)
FAISS_PATH.mkdir(parents=True, exist_ok=True)

splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CH_OVERLAP)
_embedder = TextEmbedding(model_name=EMB_MODEL)

def _embed_texts(texts: List[str]) -> List[List[float]]:
    return [vec for vec in _embedder.embed(texts)]

class RAGService:
    def __init__(self):
        self.db: Optional[FAISS] = None
        self._load_or_build()

    def _load_or_build(self):
        # пробуем загрузить
        try:
            self.db = FAISS.load_local(str(FAISS_PATH), embeddings=None,
                                       allow_dangerous_deserialization=True)
        except Exception:
            self._build_index()

    def _build_index(self):
        files = [p for p in KB_PATH.glob("*") if p.is_file() and p.suffix.lower() in {".txt", ".md"}]
        if not files:
            self.db = None
            return
        docs: List[Document] = []
        for file in files:
            text = file.read_text(encoding="utf-8", errors="ignore")
            docs.append(Document(page_content=text, metadata={"source": file.name}))
        chunks = splitter.split_documents(docs)
        # вручную собираем векторку (FAISS.from_documents ожидает Embeddings-объект, но мы даём матрицу)
        from langchain_community.vectorstores.faiss import dependable_faiss_import
        faiss = dependable_faiss_import()
        import numpy as np

        texts = [c.page_content for c in chunks]
        metas = [c.metadata for c in chunks]
        mat = np.array(_embed_texts(texts), dtype="float32")

        index = faiss.IndexFlatL2(mat.shape[1])
        index.add(mat)

        self.db = FAISS(embedding_function=None, index=index, docstore={i: Document(page_content=texts[i], metadata=metas[i]) for i in range(len(texts))}, index_to_docstore_id=list(range(len(texts))))
        self.db.save_local(str(FAISS_PATH))

    def seed(self):
        KB_PATH.mkdir(parents=True, exist_ok=True)
        seeds = {
            "onboarding.txt": "Процесс онбординга: 1) Договор, 2) Доступы, 3) Наставник. Ответственный: HR Lead.",
            "sales_regulations.txt": "Процесс продаж: лид → квалификация → демо → оффер → договор. CRM: Bitrix24.",
            "support_SLA.txt": "SLA поддержки: первая реакция — 15 минут, решение — до 8 часов. Канал: Slack #support.",
        }
        for name, txt in seeds.items():
            (KB_PATH / name).write_text(txt, encoding="utf-8")
        self._build_index()

    def ask(self, question: str) -> str:
        if self.db is None:
            return "База пустая. Загрузите FAQ-файлы в knowledge/faq или выполните /seed."
        # простая реализация similarity_search без Embeddings-объекта:
        # FAISS(embedding_function=None) не умеет .similarity_search, поэтому делаем руками
        # 1) Получаем все документы из docstore
        docs: List[Document] = [self.db.docstore[i] for i in self.db.index_to_docstore_id]
        texts = [d.page_content for d in docs]
        # 2) Вектор для вопроса
        import numpy as np
        qv = np.array(_embed_texts([question])[0], dtype="float32").reshape(1, -1)
        # 3) Поиск k ближайших
        D, I = self.db.index.search(qv, 3)
        hits: List[Dict[str, str]] = []
        for idx in I[0]:
            if idx == -1: continue
            d = docs[idx]
            hits.append({"text": d.page_content, "source": d.metadata.get("source", "faq")})
        if not hits:
            return "Ответ не найден в базе FAQ."
        return rag_answer(question, hits)
