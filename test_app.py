import chainlit as cl
import os
from dotenv import load_dotenv
import yaml
from chainlit.types import ThreadDict
from pathlib import Path
from models import AgentProfile
from chainlit.input_widget import Select, Switch, Slider

from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

# Load environment variables
load_dotenv()
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR / "config"
AGENT_PROFILES: dict[str, AgentProfile] = {}
# These are models that are avaialble from github marketplace. And work with the azure client
AVAILABLE_MODELS = [
    "gpt-4o-mini", "gpt-4o", 
    "DeepSeek-V3", "DeepSeek-R1",
    "Cohere-command-r-plus-08-2024", 
    "Llama-3.2-11B-Vision-Instruct", "Llama-3.3-70B-Instruct", "Llama-3.2-90B-Vision-Instruct", 
    "Codestral-2501", "Mistral-Large-2411", "Ministral-3B",
    "Phi-4-mini-instruct", "Phi-4-multimodal-instruct",
    
    # FOLLOWING MODELS THROW ERRORS
    # "AI21-Jamba-1.5-Mini", "AI21-Jamba-1.5-Large",
    # "Phi-4": 
    
    # FOLLOWING MODELS ARE NOT AVAILABLE FROM GITHUB MARKETPLACE
    # "claude-3.5sonnet",
    # "qwen2.5", 
    # "gemini-1.5pro"
]
# Azure OpenAI configuration
# GITHUB_PAT_TOKEN = os.getenv("GITHUB_PAT_KEY")  
# BASE_URL = os.getenv("AZURE_INFERENCE_BASE_URL")   # Azure OpenAI endpoint
CHAT_CLIENT = None
# CHAT_CLIENT = ChatCompletionsClient(
#     endpoint=BASE_URL,
#     credential=AzureKeyCredential(GITHUB_PAT_TOKEN),
# )

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

@cl.author_rename
def rename(orig_author: str):
    print(f"Renaming {orig_author}")
    rename_dict = {
        "Assistant": "my_assistant", 
        "User": "my_user",
        "System": "my_system"
    }
    return rename_dict.get(orig_author, orig_author)

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

async def update_chat_settings():
    default_settings = {
        "Model": cl.user_session.get("chat_settings", {}).get("Model", "gpt-4o-mini"),
        # "Model_index": AVAILABLE_MODELS.index(cl.user_session.get("chat_settings", {}).get("Model")) if cl.user_session.get("chat_settings", {}).get("Model") in AVAILABLE_MODELS else 0,
        "Streaming": True,
        "Temperature": 0
    }
    settings = cl.ChatSettings(
        [
            Select(
                id="Model",
                label="Model",
                values=AVAILABLE_MODELS,
                initial_index=AVAILABLE_MODELS.index(default_settings["Model"])
            ),
            Switch(id="Streaming", label="Stream Tokens", initial=default_settings["Streaming"]),
            Slider(
                id="Temperature",
                label="Temperature",
                initial=default_settings["Temperature"],
                min=0,
                max=2,
                step=0.1,
            ),
        ]
    )
    await settings.send()
    settings = cl.user_session.get("chat_settings")
    await cl.send_window_message({
        "sender": "Server",
        "message": "chat_settings_update",
        "data": settings
    })
    return settings


def get_chat_client():
    '''
    Check if the current env api key and base url match client credentials
    '''
    global CHAT_CLIENT
    user_env = cl.user_session.get("env")
    if not user_env:
        raise Exception("NOT AUTHORISED. No API_KEY or BASE_URL found")

    prev_endpoint = None if not CHAT_CLIENT else CHAT_CLIENT._config.endpoint
    prev_api_key = None if not CHAT_CLIENT else CHAT_CLIENT._config.credential._key

    if prev_endpoint != user_env["BASE_URL"] or prev_api_key != user_env["API_KEY"]:
        print(user_env["BASE_URL"])
        print(user_env["API_KEY"])
        CHAT_CLIENT = ChatCompletionsClient(
            endpoint=user_env["BASE_URL"],
            credential=AzureKeyCredential(user_env["API_KEY"]),
        )

    return CHAT_CLIENT

@cl.on_chat_start
async def start():
    #Set chat settings options
    await update_chat_settings()
    
    # Set chat history based on the chat profile
    chat_profile = cl.user_session.get("chat_profile")
    message_list = AGENT_PROFILES[chat_profile].get("message_list") if chat_profile else []
    cl.user_session.set("chat_history", message_list)


@cl.on_settings_update
async def setup_agent(settings):
    cl.user_session.set("chat_settings", settings)
    await cl.send_window_message({
        "sender": "Server",
        "message": "chat_settings_update",
        "data": settings
    })


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    cl.user_session.set("chat_history", [])
    await update_chat_settings()
    
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
        chat_settings = cl.user_session.get("chat_settings")
        chat_history.append({"role": "user", "content": message.content})   
        chat_client = get_chat_client()
        chat_response = chat_client.complete(
            messages=chat_history,
            temperature=chat_settings["Temperature"],
            stream=chat_settings["Streaming"],
            model=chat_settings["Model"]
        )
        
        if chat_settings["Streaming"]:
            msg = cl.Message(content="")
            for update in chat_response:
                if update.choices and update.choices[0].delta:
                     await msg.stream_token(update.choices[0].delta.content)

            chat_history.append({"role": "assistant", "content": msg.content})
            await msg.update()
        
        else:
            response_content = chat_response.choices[0].message.content
            chat_history.append({"role": "assistant", "content": response_content})
            await cl.Message(content=response_content).send()
    except Exception as e:
        print(f"Error: {str(e)}")
        await cl.Message(content=f"An error occurred: {str(e)}").send()

if __name__ == "__main__":
    cl.run()

