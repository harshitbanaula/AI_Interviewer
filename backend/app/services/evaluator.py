# import os
# from langchain_huggingface import HuggingFaceEndpoint
# from langchain_core.prompts import PromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# # Configuration from environment variables
# HF_TOKEN = os.getenv("HF_TOKEN")
# HF_MODEL_ID = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")
# LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.1))

# # 1. Initialize the modern HuggingFaceEndpoint
# # In 2026, task="text-generation" is the standard for completion models
# # llm = HuggingFaceEndpoint(
# #     repo_id=HF_MODEL_ID,
# #     task="text-generation",
# #     huggingfacehub_api_token=HF_TOKEN,
# #     temperature=LLM_TEMPERATURE,
# #     max_new_tokens=200,
# # )
# llm = HuggingFaceEndpoint(
#     repo_id=HF_MODEL_ID,
#     task="text-generation",
#     huggingfacehub_api_token=HF_TOKEN,
#     temperature=LLM_TEMPERATURE,
#     max_new_tokens=200,
# )
# # 2. Define the Prompt Template using the standard core module
# prompt = PromptTemplate.from_template(
#     "You are an AI interviewer.\n"
#     "Evaluate the following answer and provide constructive feedback:\n\n"
#     "{answer_text}\n\n"
#     "Provide short, clear suggestions."
# )

# # 3. Construct the Chain using LCEL (replaces ExecutionChain)
# # This uses the pipe operator to connect the prompt, model, and output parser
# feedback_chain = prompt | llm | StrOutputParser()

# def get_feedback(answer_text: str) -> str:
#     """
#     Invoke the feedback chain with the provided answer text.
#     """
#     # In 2026, use .invoke() for standard execution
#     return feedback_chain.invoke({"answer_text": answer_text})




# backend/app/services/evaluator.py
# import os
# from dotenv import load_dotenv
# load_dotenv()
# print("HF_MODEL_ID =", os.getenv("HF_MODEL_ID"))
# import os
# from langchain_huggingface import HuggingFaceEndpoint
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.messages import (
#     SystemMessage,
#     HumanMessage,
# )

# HF_TOKEN = os.getenv("HF_TOKEN")
# HF_MODEL_ID = os.getenv("HF_MODEL_ID")
# LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.1))

# llm = HuggingFaceEndpoint(
#     repo_id=HF_MODEL_ID,
#     task="conversational",  # use chat
#     huggingfacehub_api_token=HF_TOKEN,
#     temperature=LLM_TEMPERATURE,
#     max_new_tokens=200,
# )

# # Chat prompt
# template = ChatPromptTemplate.from_messages([
#     SystemMessage(content="You are an AI interviewer providing concise feedback."),
#     HumanMessage(content="{answer_text}")
# ])

# feedback_chain = template | llm | StrOutputParser()

# def get_feedback(answer_text: str) -> str:
#     return feedback_chain.invoke({"answer_text": answer_text})




# backend/app/services/evaluator.py
import os
from dotenv import load_dotenv

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.1))

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN missing")

# 1 Create HF endpoint (provider-level)
hf_endpoint = HuggingFaceEndpoint(
    repo_id=HF_MODEL_ID,
    task="conversational",
    huggingfacehub_api_token=HF_TOKEN,
    temperature=LLM_TEMPERATURE,
    max_new_tokens=200,
)

# 2 Wrap it as a CHAT model ✅
llm = ChatHuggingFace(llm=hf_endpoint)

# 3 Chat prompt (NOT PromptTemplate)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI interviewer. Give short, constructive feedback."),
    ("human", "{answer_text}")
])

# 4LCEL pipe
feedback_chain = prompt | llm | StrOutputParser()

def get_feedback(answer_text: str) -> str:
    return feedback_chain.invoke({"answer_text": answer_text})
