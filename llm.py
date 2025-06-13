from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    Settings,
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

model = "llama3.2:1b"
llm = Ollama(
    model=model,
    request_timeout=120.0,
    context_window=16000,
)

# ensures the model is used as the underlying language model for generating embeddings
Settings.llm = llm
Settings.embed_model = OllamaEmbedding(
    model_name=model,
    base_url="http://localhost:11434",  # default Ollama local server URL
    ollama_additional_kwargs={"mirostat": 0},  # optional parameters
)

# Load pulp docs and create a vector index
documents = SimpleDirectoryReader("./docs").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()


def run_llm(question):
    # Query the vector index
    retrieved_response = query_engine.query(question)
    context_text = str(retrieved_response)

    # Construct the augmented prompt combining context and question
    augmented_prompt = f"""
    Use the following context from the documents to answer the question:

    {context_text}

    Question: {question}
    Answer:
    """

    # Call the LLM with the augmented prompt
    return llm.complete(augmented_prompt)
