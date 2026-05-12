from google.adk.agents import Agent
from .retriever import search_docs

root_agent = Agent(name = "rag_agent",
                model = "gemini-2.5-flash",
                instruction = "You are a helpful assistant that can answer questions about the documents.",
                tools = [search_docs])