import os
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
from langchain_core.vectorstores import VectorStoreRetriever

def get_interests_rag_chain(vector_store_retriever: VectorStoreRetriever):
    llm_name = os.getenv("INTERESTS_RAG_LLM")

    if not llm_name:
        raise ValueError("INTERESTS_RAG_LLM environment variable not set")

    RAG_PROMPT = """\
      Contexto:
      {context}

      Con base en el contexto proporcionado, responde a la siguiente pregunta:
      {question}

      Si no hay suficiente información en el contexto para responder la pregunta, responde que no sabes la respuesta. Responde la pregunta con una lista numerada.
    """

    rag_prompt_template = ChatPromptTemplate.from_template(RAG_PROMPT)
    
    rag_llm = ChatOpenAI(
        model=llm_name,
        temperature=0
    )

    # Define a function to retrieve context based on the question
    def retrieve_context(inputs):
        question = inputs["question"]
        return vector_store_retriever.invoke(question)

    # Create the RAG chain using the current API
    return (
        RunnablePassthrough()
        | {"context": retrieve_context, "question": itemgetter("question")}
        | rag_prompt_template
        | rag_llm
        | StrOutputParser()
    )