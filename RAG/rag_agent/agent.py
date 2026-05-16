from google.adk.agents import Agent
from .retriever import search_docs, get_last_search

retriever_agent = Agent(
    name = "retriever_agent",
    model = "gemini-2.5-flash",
    description = "Handles questions that require searching local documents",
    instruction = """
    You are a retriever agent that can search local documents for relevant context.
    You will be given a question and you need to search the local documents for relevant context.
    You will then return the relevant context to the user.
    """,
    tools = [search_docs]
)

memory_agent = Agent(
    name = "memory_agent",
    model = "gemini-2.5-flash",
    description = "Handles memory and context management for the rag system",
    instruction = """
        You are a session memory specialist
        Use get_last_search when the user asks about previous searches, last query, or queries searched so far.
        Keep the answers short and direct. 
    """,
    tools = [get_last_search]
)

root_agent = Agent(name = "coordinator_agent",
                model = "gemini-2.5-flash",
                instruction = """
                You are a helpful coordinator for a local RAG system.
                For document questions, route to retriever_agent.
                For questions about previous searches or query history, route to memory_agent.
                """,
                sub_agents = [retriever_agent, memory_agent]
)



