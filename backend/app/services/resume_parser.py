# # backend/app/services/resume_parser.py
# import os
# from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

# from langchain_text_splitters import CharacterTextSplitter

# def parse_resume(file_path: str):
#     """
#     Load resume file (PDF, DOCX, TXT) and return extracted text.
#     """
#     ext = os.path.splitext(file_path)[1].lower()

#     if ext == ".pdf":
#         loader = PyPDFLoader(file_path)
#     elif ext == ".docx":
#         loader = Docx2txtLoader(file_path)
#     elif ext == ".txt":
#         loader = TextLoader(file_path)
#     else:
#         raise ValueError("Unsupported file type. Use PDF, DOCX, or TXT.")

#     docs = loader.load()
#     splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
#     text_chunks = splitter.split_documents(docs)
#     full_text = " ".join([chunk.page_content for chunk in text_chunks])
#     return full_text


import os 
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
import tempfile
def parse_resume(filename: str, content_bytes: bytes) -> str:
    """
    Parse resume content using LangChain loaders.
    Supports PDF, DOCX, TXT.
    """

    suffix = filename.split(".")[-1].lower()

    # Create temp file safely (cross-platform)
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(content_bytes)
        tmp_path = tmp.name

    try:
        if suffix == "pdf":
            loader = PyPDFLoader(tmp_path)
        elif suffix in ["docx", "doc"]:
            loader = Docx2txtLoader(tmp_path)
        elif suffix == "txt":
            loader = TextLoader(tmp_path)
        else:
            raise ValueError("Unsupported resume format")

        docs = loader.load()
        resume_text = "\n".join(doc.page_content for doc in docs)
        return resume_text

    finally:
        os.remove(tmp_path)
