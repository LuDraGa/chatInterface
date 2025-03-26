import chainlit as cl
import base64
from open_file_converse.clients_and_connectors import datastore_creator, get_datastores_list

def base64_to_file(file_base64_string):
    # If your base64 string has a data URL prefix (e.g., "data:text/plain;base64,..."),
    # remove it before decoding.
    if file_base64_string.startswith("data:"):
        base64_str = file_base64_string.split(",", 1)[1]
    else:
        base64_str = file_base64_string

    # Decode the base64 string back to bytes.
    decoded_bytes = base64.b64decode(base64_str)

    # If the file is a text file, try decoding to a UTF-8 string.
    try:
        file_contents = decoded_bytes.decode("utf-8")
    except UnicodeDecodeError:
        # If decoding fails, leave it as bytes (or handle as needed).
        file_contents = decoded_bytes
    return file_contents

@cl.action_callback("create_rag_datastore")
async def create_rag_datastore(action: cl.Action):
    print("In create data store")
    payload = action.payload
    try:
        datastore_name = payload["datastore_name"]
        # embeddings_model = payload["embeddings_model"]
        files_list = payload.get("datastore_input_files", [])
        urls_list = payload.get("datastore_input_urls", [])
        datastore_description = payload.get("description", "")

        data_sources = []
        if len(files_list) > 0:
            for file in files_list:
                print(file["name"])
                data_sources.append({"type": "base64", "data": file["content"], "name": file["name"]})
        if len(urls_list) > 0:
            for url in urls_list:   
                data_sources.append({"type": "url", "data": url})

        datastore_manager, vector_store = datastore_creator(datastore_name, datastore_description, data_sources)

        print("In create data store")
        ds_list = get_datastores_list()
        if datastore_name in ds_list:
            await cl.user_session.set("datastores_list", ds_list)
            await cl.send_window_message({
                "sender": "Server",
                "message": "datastores_list_update",
                "data": ds_list
            })
            # await cl.Message(content=f"Datastore {datastore_name} created successfully").send()
            return "Datastore created successfully"
        else:
            # await cl.Message(content=f"Datastore {datastore_name} creation failed").send()
            return "Failed to create datastore"
    except Exception as e:
        # await cl.Message(content=f"Datastore {datastore_name} creation failed").send()
        return "Failed to create datastore \nERROR: " + str(e)
    
@cl.on_window_message
async def select_datastore(request):
    sender = request["sender"]
    message = request["message"]
    data = request["data"]
    if sender == "UI server" and message == "selected_datastore":
        cl.user_session.set("selected_datastore", data)
    else:
        print(f"\n\nIn select datastore")
        print(f"Message from {sender}: {message}")
        print(f"\n\n")
        return

async def run_open_file_converse(message: str, chat_settings: dict):
    params = { 
        "default" : [
            "placement"
            "name", 
            "type",
            "title",
            "tooltip"
        ],
        "text/int": ["placeholder", "required"],
        "switch": ["defaultChecked"],
        "select": ["options"]
    }


    # Create Datastore
    cde_props = {
        "config": [
            {
                "type": "text",
                "title": "Datastore Name",
                "name": "datastore_name",
                "placeholder": "Agents and Orchestration",
                "required": True,
                "tooltip": "Datastore Name",
                "placement": "left"
            },
            # {
            #     "type": "int",
            #     "title": "Datastore Version",
            #     "name": "datastore_version",
            #     "placeholder": "1",
            #     "required": True,
            #     "tooltip": "Datastore Version",
            #     "placement": "right"
            # },
            # {
            #     "placement": "left",
            #     "name": "is_private",
            #     "type": "switch",
            #     "title": "Private",
            #     "tooltip": "Datastore visiblity",
            #     "defaultChecked": False
            # },
            {
                "placement": "left",
                "name": "description",
                "type": "textarea",
                "title": "Description",
                "tooltip": "Datastore description or purpose",
                "placeholder": "Datastore for agents and orchestration. It contains: \n - Blogs \n - Research papers \n - Reports",
                "rows": 5
            },
            {
                "type": "files_input",
                "title": "Datastore Input",
                "name": "datastore_input",
                "description": "Add files to the datastore",
                "fields": [
                    {
                        "type": "text",
                        "title": "File Name",
                        "placeholder": "Enter the name of the file",
                        "required": False,
                        "tooltip": "File Name",
                        "placement": "left"
                    }
                ]
            }
        ]
        
    }
    create_datastore_form = cl.CustomElement(name="CreateDatastore", props=cde_props)
    
    async with cl.Step(
            name="Parent step", 
            elements=[create_datastore_form],
            default_open=True,
            show_input=True,
        ) as step:
        step.input = "Register a datastore"
        # step.output = "Parent step output"
        # await cl.Message(content="Here is the third!", elements=[ticket_element_3]).send()

    # After the step, retrieve the updated element
    
    # await cl.sleep(5)

    # step.output += "\n\nParent step output updated"
    # await step.update()

    # async with cl.Step(name="Test") as step:
    #     # Sending an action button within a chatbot message
    #     step.input = "Select Datastore" 
    #     actions = [
    #         cl.Action(name="select_datastore_button", payload={"value": "example_value"}, label="Choose Datastore"),
    #         cl.Action(name="add_datastore_button", payload={"value": "example_value"}, label="Create New Datastore")
    #     ]

    #     await cl.Message(content="Interact with this action button:", actions=actions).send()
