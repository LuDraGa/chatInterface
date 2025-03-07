import chainlit as cl
from openai import AsyncOpenAI, OpenAI
import os
from dotenv import load_dotenv
import yaml
from typing import Optional, List
from chainlit.types import ThreadDict
from pathlib import Path
from models import AgentProfile

# Load environment variables
load_dotenv()
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
AGENT_PROFILES: dict[str, AgentProfile] = {}

# Azure OpenAI configuration
api_key = os.getenv("AZURE_OPENAI_API_KEY")  # Your GitHub PAT
base_url = os.getenv("AZURE_OPENAI_BASE_URL")  # Azure OpenAI endpoint

# Initialize OpenAI client with Azure configuration
client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,
    # default_headers={
    #     "api-version": "2023-05-15"  # Azure OpenAI API version
    # }
)

# Instrument the OpenAI client
cl.instrument_openai()


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Load users from the YAML file
    with open(CONFIG_DIR / "user_credentials.yaml", "r") as file:
        data = yaml.safe_load(file)
    # Iterate over the user list
    for user in data.get("users", []):
        if user["username"] == username and user["password"] == password:
            return cl.User(
                identifier=username, metadata={"role": user["role"], "provider": "yaml"}
            )
    return None

@cl.step(type="tool")
async def get_user_info(user_id: str):
    return {"name": "John Doe", "age": 30, "email": "john.doe@example.com"}

@cl.set_chat_profiles
async def chat_profile():
    # Load chat profiles from YAML config
    with open(CONFIG_DIR / "chat_agent_profiles.yaml", "r") as file:
        profiles_data = yaml.safe_load(file)
    
    chat_profiles = []
    for profile in profiles_data.get("agent_profiles", []):
        AGENT_PROFILES[profile.get("name")] = profile
        chat_profiles.append(
            cl.ChatProfile(
                name=profile.get("name"),
                markdown_description=profile.get("description", ""),
                icon=profile.get("icon"),
                default=profile.get("default", False),
                starters=profile.get("starters")
            )
        )
    
    return chat_profiles

@cl.on_chat_start
async def start():
    chat_profile = cl.user_session.get("chat_profile")
    message_list = AGENT_PROFILES[chat_profile].get("message_list") if chat_profile else []
    cl.user_session.set("chat_history", message_list)
    await cl.Message(content=f"Let's start the personality test by the {chat_profile}?").send()

@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    cl.user_session.set("chat_history", [])

    # user_session = thread["metadata"]
    
    for message in thread["steps"]:
        if message["type"] == "user_message":
            cl.user_session.get("chat_history").append({"role": "user", "content": message["output"]})
        elif message["type"] == "assistant_message":
            cl.user_session.get("chat_history").append({"role": "assistant", "content": message["output"]})


@cl.on_message
async def on_message(message: cl.Message):
    try:
    # Note: by default, the list of messages is saved and the entire user session is saved in the thread metadata
        chat_history = cl.user_session.get("chat_history")
        chat_history.append({"role": "user", "content": message.content})   
        chat_response = await client.chat.completions.create(
                model="gpt-4o",  
                # model="gpt-4ox",  #changed to fail till rest of the code is written
                messages=chat_history,
                temperature=0.7,
            )
        response_content = chat_response.choices[0].message.content
        chat_history.append({"role": "assistant", "content": response_content})
        await cl.Message(content=response_content).send()
    except Exception as e:
        print(f"Error: {str(e)}")
        await cl.Message(content=f"An error occurred: {str(e)}").send()

if __name__ == "__main__":
    cl.run()

