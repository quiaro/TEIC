import os
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.utils.mocks import MockCompanyCultureModel
from app.utils.chunks import getFirstChunkFromFile
from langchain_community.vectorstores.qdrant import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from app.utils.chunks import chunkTimeStampedFile

async def get_company_culture(model: str, data_files: list[str]):
    if os.getenv("ENV", "development").lower() == "development":
        openai_chat_model = MockCompanyCultureModel()
    else:
        openai_chat_model = ChatOpenAI(model=model)

    # Get first chunk from each file and join them
    conversations = "\n".join(
        line
        for file in data_files
        for chunk in [getFirstChunkFromFile(
            file,
            r"\[(\d{1,2}/\d{1,2}/\d{2}), \d{1,2}:\d{2}:\d{2}(?:.AM|.PM)?\]",
            "%d/%m/%y",
            "day"
        )]
        for line in chunk
    )

    COMPANY_CULTURE_PROMPT = """\
    Eres un psicólogo experto en psicología laboral. Se necesita que analices las siguientes conversaciones con el objetivo de resumir el tipo de cultura que se observa en la empresa. Enfocate en los aspectos positivos de la cultura de la empresa y obvia los aspectos negativos. Resume el ambiente de la empresa en una oración.

    ### Conversaciones
    {conversations}
    """

    company_culture_prompt = ChatPromptTemplate.from_template(COMPANY_CULTURE_PROMPT)
    company_culture_chain = company_culture_prompt | openai_chat_model
    
    return await company_culture_chain.ainvoke({"conversations": conversations})


async def get_conversations_retriever(data_files: list[str], collection_name: str, k: int):
  model_name = os.getenv("EMBEDDING_MODEL")
  embedding_dim = os.getenv("EMBEDDING_DIM")
  timeStampRegex = r"\[(\d{1,2}/\d{1,2}/\d{2}), \d{1,2}:\d{2}:\d{2}(?:.AM|.PM)?\]"
  dateRegex = "%d/%m/%y"
  interval = "week"
  overlap = 2

  if not model_name:
    raise ValueError("EMBEDDING_MODEL environment variable not set")

  if not embedding_dim:
    raise ValueError("EMBEDDING_DIM environment variable not set")

  try:
      # Convert embedding_dim to integer
      embedding_dim = int(embedding_dim)
      
      embedding_model = HuggingFaceEmbeddings(model_name=model_name, model_kwargs={"trust_remote_code": True}, encode_kwargs={"normalize_embeddings": True})
      client = QdrantClient(":memory:")
      client.create_collection(
          collection_name=collection_name,
          vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
      )

      vector_store = Qdrant(
          client=client,
          collection_name=collection_name,
          embeddings=embedding_model,
      )
      
      for filepath in data_files:  
          chunks = []
          for i, (start, end, lines) in enumerate(chunkTimeStampedFile(
              filepath, timeStampRegex, dateRegex, interval, overlap
          )):
              if (len(lines) > 0):
                  chunk = "".join(lines)
                  chunks.append(chunk)
          
          if os.getenv("DEBUG", "false").lower() == "true":
              print(f"Adding {len(chunks)} chunks from {filepath}")
          vector_store.add_texts(chunks)
      
      return vector_store.as_retriever(search_kwargs={"k": k})  

  except Exception as e:
      # Raise the exception instead of returning it as a string
      raise Exception(f"Error creating vector store retriever: {str(e)}")
