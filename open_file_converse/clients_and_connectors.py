import os
import base64
import binascii
import tempfile
import lancedb
from langchain_community.vectorstores import LanceDB
from langchain_unstructured import UnstructuredLoader
from langchain_community.document_loaders import DirectoryLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from time import time
# -----------------------------
# Utility function to convert base64 string to file content
# -----------------------------
def base64_to_file(file_base64_string):
    # If your base64 string has a data URL prefix (e.g., "data:text/plain;base64,..."),
    # remove it before decoding.
    if file_base64_string.startswith("data:"):
        base64_str = file_base64_string.split(",", 1)[1]
    else:
        base64_str = file_base64_string

    # Decode the base64 string back to bytes.
    decoded_bytes = base64.b64decode(base64_str)

    # If the file is a text file, try decoding to a UTF-8 string.
    try:
        file_contents = decoded_bytes.decode("utf-8")
    except UnicodeDecodeError:
        # If decoding fails, leave it as bytes (or handle as needed).
        file_contents = decoded_bytes
    return file_contents

# -----------------------------
# Generic Model and Embeddings Loader
# -----------------------------
def load_llm(model_provider: str, base_url: str, api_key: str, model_name: str, **kwargs):
    """
    Generic LLM loader.
    Example usage:
      load_llm("azure", azure_base_url, github_pat, "gpt-4o", api_version="2025-02-01-preview")
    """
    if model_provider.lower() == "azure":
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_endpoint=base_url, 
            api_key=api_key, 
            model=model_name, 
            **kwargs
        )
    elif model_provider.lower() == "openai":
        from langchain.chat_models import ChatOpenAI
        return ChatOpenAI(api_key=api_key, model=model_name, **kwargs)
    # Extend for other providers (anthropic, ollama, etc.)
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")

def load_embeddings(model_provider: str, base_url: str, api_key: str, model_name: str, **kwargs):
    """
    Generic embeddings model loader.
    """
    if model_provider.lower() == "azure":
        from langchain_openai import AzureOpenAIEmbeddings
        return AzureOpenAIEmbeddings(
            azure_endpoint=base_url, 
            api_key=api_key, 
            model=model_name, 
            **kwargs
        )
    elif model_provider.lower() == "openai":
        from langchain.embeddings import OpenAIEmbeddings
        return OpenAIEmbeddings(api_key=api_key, model=model_name, **kwargs)
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")

# -----------------------------
# DataStoreManager: Storage Part
# -----------------------------
class DataStoreManager:
    def __init__(self, db_path: str, embeddings_model):
        """
        Initialize with a local LanceDB path and an embeddings model.
        """
        self.db_path = db_path
        self.embeddings_model = embeddings_model
        # Connect to or initialize a local LanceDB database
        self.db = lancedb.connect(db_path)
    
    def list_datastores(self):
        """
        List the names of all stored datastores.
        """
        return list(self.db.table_names())

    
    def create_datastore(self, name: str, description: str, data_sources: list, text_splitter=None):
        """
        Create a new datastore by processing data sources.
        
        data_sources: list of dicts with keys:
          - 'type': 'base64', 'file_path', or 'url'
          - 'data': the actual data (e.g., file path, URL, or base64 encoded string or file content)
        """
        documents = []
        for source in data_sources:
            src_type = source.get("type")
            content = source.get("data")
            
            if src_type == "base64":
                # Try to validate if the string is a base64 encoded value.
                try:
                    # This will raise an exception if the string contains invalid base64 characters.
                    base64.b64decode(content, validate=True)
                    # If validation passes, convert using your helper function.
                    file_content = base64_to_file(content)
                    print(file_content)
                except (binascii.Error, ValueError):
                    # If validation fails, assume content is already the original file content.
                    file_content = content
                
                # Write file_content to a temporary file to use with the loader.
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
                    if isinstance(file_content, str):
                        tmp_file.write(file_content.encode("utf-8"))
                    else:
                        tmp_file.write(file_content)
                    tmp_file_path = tmp_file.name
                loader = UnstructuredLoader(tmp_file_path)
                docs = loader.load()
                os.unlink(tmp_file_path)  # Clean up the temporary file
                documents.extend(docs)
            elif src_type == "file_path":
                # Load from a local file
                loader = UnstructuredLoader(content)
                docs = loader.load()
                documents.extend(docs)
            elif src_type == "url":
                loader = WebBaseLoader(content)
                docs = loader.load()
                documents.extend(docs)
            else:
                print(f"Unsupported source type: {src_type}")
        
        # Use default text splitter if none provided
        if not text_splitter:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        
        # Split documents into chunks
        split_docs = text_splitter.split_documents(documents)
        
        # Tag each chunk with metadata for source and datastore info
        for doc in split_docs:
            if not doc.metadata:
                doc.metadata = {}
            doc.metadata.update({
                "datastore_name": name,
                "datastore_description": description,
                # Additional tagging (e.g., file name, source URL) can be added here
            })
        
        # Create a LanceDB vector store collection from the processed chunks
        vector_store = LanceDB(
            connection=self.db,
            embedding=self.embeddings_model,
            table_name=name,
            mode="append"
        )
        # Add documents in chunks to avoid overwhelming the embedding model
        print(self.list_datastores())
        chunk_size = 5  # Adjust based on embedding model limits
        for i in range(0, len(split_docs), chunk_size):
            print(f"Adding chunk {i} of {len(split_docs)}")
            chunk = split_docs[i:i + chunk_size]
            vector_store.add_documents(chunk)
            time.sleep(2)
        print(f"Datastore {name} created successfully")
        print(self.list_datastores())
        return vector_store

# -----------------------------
# RAGRetriever: Retrieval Part
# -----------------------------
class RAGRetriever:
    def __init__(self, vector_store: LanceDB, embeddings_model, llm):
        """
        Initialize the retriever with a specific vector store, embeddings model, and LLM.
        """
        self.vector_store = vector_store
        self.embeddings_model = embeddings_model
        self.llm = llm
        
    def query(self, query_text: str, top_k: int = 5):
        """
        Retrieval-Augmented Generation (RAG) workflow:
          1. Query -> embedding -> vector store similarity search.
          2. Aggregate retrieved chunks and pass context to LLM.
        
        Returns:
          - LLM response
          - The list of retrieved document chunks (with metadata)
        """
        retrieved_docs = self.vector_store.similarity_search(query_text, k=top_k)
        
        # Prepare context (for example, concatenate retrieved content)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        prompt = f"Context:\n{context}\n\nQuestion: {query_text}\nAnswer:"
        response = self.llm(prompt)
        return response, retrieved_docs

BASE_URL = os.getenv("AZURE_INFERENCE_BASE_URL")
API_KEY = os.getenv("GITHUB_PAT_KEY")
# import os
# os.environ['USER_AGENT'] = 'MyLangChainApp/1.0'

DB_BASE_PATH = Path(__file__).parent.parent / "lancedb_storage"
LLM_QNA_MODEL = load_llm("azure", BASE_URL, API_KEY, "gpt-4o", api_version="2025-02-01-preview")
EMBEDDINGS_MODEL = load_embeddings("azure", BASE_URL, API_KEY, "text-embedding-3-large", api_version="2024-02-15-preview")
datastore_manager = DataStoreManager(DB_BASE_PATH, EMBEDDINGS_MODEL)

def datastore_creator(datastore_name: str, datastore_description: str, data_sources: list):
    vector_store = datastore_manager.create_datastore(datastore_name, datastore_description, data_sources)
    return datastore_manager, vector_store
    # data_sources = [
    #     {"type": "file_path", "data": "./sample.txt"},
    #     {"type": "url", "data": "https://example.com/sample"}
    #     # {"type": "base64", "data": "SGVsbG8gd29ybGQh"}  # example base64 for "Hello world!"
    # ]

def get_datastores_list():
    return datastore_manager.list_datastores()

def datastore_retriever(datastore_name: str, question: str):
    db = lancedb.connect(DB_BASE_PATH)
    vector_store = LanceDB(
        connection=db,
        embedding=EMBEDDINGS_MODEL,
        table_name=datastore_name
    )
    retriever = RAGRetriever(vector_store, EMBEDDINGS_MODEL, LLM_QNA_MODEL)
    answer, retrieved_docs = retriever.query(question)
    return answer, retrieved_docs

# -----------------------------
# Example Usage
# -----------------------------
# if __name__ == "__main__":
#     example_url = "https://farzzy.hashnode.dev/mastering-agentic-rag-multi-tool-orchestration-for-ai-agents-part-2"
#     example_file = "/Users/abhiroopprasad/code/side-projects/psych_clone/open_deep_research/configuration.py"
#     example_base64 = base64.b64encode(open(example_file, "rb").read()).decode("utf-8")
    
#     ds_name = "example_datastore"
#     ds_description = "Example datastore with text and web content."
#     data_sources = [
#         {"type": "file_path", "data": example_file},
#         {"type": "url", "data": example_url},
#         {"type": "base64", "data": example_base64}
#     ]

#     datastore_manager = DataStoreManager(DB_BASE_PATH, EMBEDDINGS_MODEL)
    
#     datastore_manager, vector_store = datastore_creator(datastore_manager, ds_name, ds_description, data_sources)
#     print(datastore_manager.list_datastores())

#     answer, retrieved_docs = datastore_retriever(ds_name, "What is the content about?")
#     print(answer)
#     print(retrieved_docs)
