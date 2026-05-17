import os

from google.adk.agents import Agent
import datetime
from zoneinfo import ZoneInfo

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def get_weather(city):
    """ Returns the current weather in a specified city
    Args:
        city (str): The name of the city to get the weather for

    Returns:
        dict: A dictionary containing the status, city, and current weather
    """
    if city.lower() == "new york":
        return {
            "status": "success",
            "report" : (
                "The weather in New York is really sunny with a temperature of 25 degrees Celsius. "
                "It's a great day to be outside and enjoy the sunshine!"
            ),
        }
    else:
        return {"status": "error", "message": f"Sorry, I don't have weather information for {city}."}

def get_current_time(city):
    """ Returns the current time in a specified city
    Args:
        city (str): The name of the city to get the time for
    
    Returns:
        dict: A dictionary containing the status, city, and current time
    
    """
    if city.lower() == "new york":
        tz = ZoneInfo("America/New_York")
        current_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "status": "success",
            "report": f"The current time in New York is {current_time}."
        }
    else:
        return {"status": "error", "message": (f"Sorry, I don't have the timezone information for the {city}")}
    

root_agent = Agent(
    model=MODEL,
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction="""
    You are a RAG agent
    Answer user questions to the best of your knowledge""",
    tools = {
        get_current_time, get_weather
    }
)

