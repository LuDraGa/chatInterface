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

from tavily import TavilyClient
from literalai import LiteralClient

from open_deep_research.adapter import run_open_deep_research


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
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY") 
LITERAL_API_KEY = os.getenv("LITERAL_API_KEY") 

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
# literalai_client = LiteralClient(api_key=LITERAL_API_KEY) 
# GITHUB_PAT_TOKEN = os.getenv("GITHUB_PAT_KEY")  
# BASE_URL = os.getenv("AZURE_INFERENCE_BASE_URL")   # Azure OpenAI endpoint
# CHAT_CLIENT = ChatCompletionsClient(
#     endpoint=BASE_URL,
#     credential=AzureKeyCredential(GITHUB_PAT_TOKEN),
# )

# workflow = StateGraph(state_schema=MessagesState)
CHAT_CLIENT = None

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



# Commands to  add datas store
commands = [
    # {"id": "Picture", "icon": "image", "description": "Use DALL-E"},
    # {"id": "Search", "icon": "globe", "description": "Find on the web"},
    # {
    #     "id": "Canvas",
    #     "icon": "pen-line",
    #     "description": "Collaborate on writing and code",
    # },
    # {
    #     "id": "Dataset",
    #     "icon": "database",
    #     "description": "Add/update Datastore",
    # },
    # {
    #     "id": "RAG",
    #     "icon": "layers",
    #     "description": "Contextual Search with granular source citations",
    # },
    {
        "id": "OpenDeepSearch",
        "icon": "search",
        "description": "Helps browse deeply and gives a final report",
    },
    {
        "id": "CodeInsightSolver",
        "icon": "code",
        "description": "Converse and edit codebase: Git url or upload files from local",
    },
    {
        "id": "TextDocsConverser",
        "icon": "text-document",
        "description": "Converse and edit text files: Upload files from local: PDF, DOCX, TXT, MD",
    },
    {
        "id": "DeepResearch",
        "icon": "microscope",
        "description": "Does indepth independent research and gives a final report",
    }
]

@cl.on_chat_start
async def start():
    await cl.context.emitter.set_commands(commands)
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
    await cl.context.emitter.set_commands(commands)
    cl.user_session.set("chat_history", [])
    await update_chat_settings()
    
    for message in thread["steps"]:
        if message["type"] == "user_message":
            cl.user_session.get("chat_history").append({"role": "user", "content": message["output"]})
        elif message["type"] == "assistant_message":
            cl.user_session.get("chat_history").append({"role": "assistant", "content": message["output"]})
    


# from langchain_core.messages import HumanMessage, AIMessageChunk
# from langchain_core.runnables.config import RunnableConfig
# from langchain_openai import ChatOpenAI

# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.graph import START, MessagesState, StateGraph

# workflow = StateGraph(state_schema=MessagesState)
# model = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("AZURE_OPENAI_BASE_URL"), model="gpt-4o-mini", temperature=0)

# def call_model(state: MessagesState):
#     response = model.invoke(state["messages"])
#     return {"messages": response}

# workflow.add_edge(START, "model")
# workflow.add_node("model", call_model)

# memory = MemorySaver()

# app = workflow.compile(checkpointer=memory)
from langgraph.checkpoint.memory import MemorySaver
from open_deep_research.graph import builder
from langgraph.types import Command
import uuid 
from IPython.display import Image, display
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


@cl.on_message
async def on_message(message: cl.Message):
    try:
    # Note: by default, the list of messages is saved and the entire user session is saved in the thread metadata
        chat_history = cl.user_session.get("chat_history")
        chat_settings = cl.user_session.get("chat_settings")
        chat_history.append({"role": "user", "content": message.content})   
        chat_client = get_chat_client()


        if message.command == "OpenDeepSearch":
            display(Image(graph.get_graph().draw_mermaid_png()))
            await run_open_deep_research(message.content, graph, chat_settings)
            await cl.Message(content="OpenDeepSearch completed").send()
            return 
            # await step.send()
            # TODO: This is important.. can create a step dict
            #  await cl.context.emitter.send_ask_user()
        
        
        # await cl.Message(content="Not doing deep research").send()

        else:
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

