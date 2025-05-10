from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import os
from app.utils.mocks import MockCompanyCultureModel

async def get_company_culture(model: str, conversations: str):
    if os.getenv("ENV", "development").lower() == "development":
        openai_chat_model = MockCompanyCultureModel()
    else:
        openai_chat_model = ChatOpenAI(model=model)

    COMPANY_CULTURE_PROMPT = """\
    Eres un psicólogo experto en psicología laboral. Se necesita que analices las siguientes conversaciones con el objetivo de resumir el tipo de cultura que se observa en la empresa. Enfocate en los aspectos positivos de la cultura de la empresa y obvia los aspectos negativos. Resume el ambiente de la empresa en una oración.

    ### Conversaciones
    {conversations}
    """

    company_culture_prompt = ChatPromptTemplate.from_template(COMPANY_CULTURE_PROMPT)
    company_culture_chain = company_culture_prompt | openai_chat_model
    
    return await company_culture_chain.ainvoke({"conversations": conversations})