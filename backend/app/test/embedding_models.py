import os
import asyncio
import json
from langgraph.graph import START, StateGraph
from typing_extensions import List, TypedDict
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from app.utils.chunks import chunkTimeStampedFile, clean_up_string
from app.setup.environment import setup
from ragas import EvaluationDataset, evaluate, RunConfig
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness, ResponseRelevancy, ContextEntityRecall, NoiseSensitivity
import pandas as pd

# Call setup to initialize environment
setup()

class State(TypedDict):
  question: str
  context: List[str]
  response: str

model_name = os.getenv("ANSWERS_LLM")
llm = ChatOpenAI(model=model_name, temperature=0)

async def get_conversations_retriever(model_name: str, data_files: list[str], k: int):
  embedding_dim = os.getenv("EMBEDDING_DIM")
  timeStampRegex = r"\[(\d{1,2}/\d{1,2}/\d{2}), \d{1,2}:\d{2}:\d{2}(?:.AM|.PM)?\]"
  dateRegex = "%d/%m/%y"
  interval = "week"
  overlap = 2
  collection_name = "test_collection"

  if not embedding_dim:
    raise ValueError("EMBEDDING_DIM environment variable not set")

  try:
      embedding_model = HuggingFaceEmbeddings(model_name=model_name)
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
          for i, (_, _, lines) in enumerate(chunkTimeStampedFile(
              filepath, timeStampRegex, dateRegex, interval, overlap
          )):
              if (len(lines) > 0):
                  chunk_text = "".join(lines)
                  removePatterns = {
                    "timeStampRegex": timeStampRegex,
                  }
                  chunk_text = clean_up_string(chunk_text, removePatterns)
                  chunks.append(chunk_text)
                  
          if os.getenv("DEBUG", "false").lower() == "true":
              print(f"Adding {len(chunks)} chunks from {filepath}")
          vector_store.add_texts(chunks)
      
      return vector_store.as_retriever(search_kwargs={"k": k})  

  except Exception as e:
      return str(e)


def build_test_graph(retriever: VectorStoreRetriever):

    ANSWER_PROMPT = """
    Eres un asistente que responde preguntas basándose únicamente en el contexto proporcionado. Tu respuesta debe ser concisa y al punto. Si la información para responder la pregunta no está contenida en el contexto, responde con "No lo sé". No uses conocimiento externo ni hagas suposiciones más allá de lo que está en el contexto.

    Contexto:
    {context}

    Pregunta:
    {question}

    Respuesta:
    """

    prompt_template = ChatPromptTemplate.from_template(ANSWER_PROMPT)

    def retrieve(state):
        retrieved_chunks = retriever.invoke(state["question"])
        return {"context" : retrieved_chunks}

    def answer(state):
        chunks = "\n\n".join([chunk.page_content for chunk in state["context"]])
        messages = prompt_template.format_messages(question=state["question"], context=chunks)
        response = llm.invoke(messages)
        return {"response" : response.content}

    graph_builder = StateGraph(State).add_sequence([retrieve, answer])
    graph_builder.add_edge(START, "retrieve")
    return graph_builder.compile()


if __name__ == "__main__":
    baseline_embedding_model = os.getenv("EMBEDDING_MODEL")

    if not baseline_embedding_model:
        raise ValueError("EMBEDDING_MODEL environment variable not set")

    judge_model_name = os.getenv("JUDGE_LLM")

    if not judge_model_name:
        raise ValueError("JUDGE_LLM environment variable not set")

    data_files = [
        "app/data/_chat_abel_mesén.txt",
        "app/data/_chat_francisco_salas.txt",
        "app/data/_chat_grettel.txt",
        "app/data/_chat_laura_monestel.txt",
        "app/data/_chat_luisa_alfaro.txt",
        "app/data/_chat_maria_jose_alfaro.txt",
        "app/data/_chat_maritza_ortiz.txt",
        "app/data/_chat_paola_mora_lopez.txt",
        "app/data/_chat_robert_monestel.txt",
    ]

    custom_run_config = RunConfig(timeout=360)
    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model=judge_model_name))

    retriever = asyncio.run(get_conversations_retriever(baseline_embedding_model, data_files, 6))
    graph = build_test_graph(retriever)

    with open("app/test/test_samples.json", "r") as f:
        data = json.load(f)
        samples = data["samples"]
    
        for sample in samples:
            response = graph.invoke({"question": sample["user_input"]})
            sample["response"] = response["response"]
            sample["retrieved_contexts"] = [chunk.page_content for chunk in response["context"]]

        dataset = pd.DataFrame(samples)
        evaluation_dataset = EvaluationDataset.from_pandas(dataset)

        result = evaluate(
            dataset=evaluation_dataset,
            metrics=[LLMContextRecall(), Faithfulness(), FactualCorrectness(), ResponseRelevancy(), ContextEntityRecall(), NoiseSensitivity()],
            llm=evaluator_llm,
            run_config=custom_run_config
        )

        print(result)
