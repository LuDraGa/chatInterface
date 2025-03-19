import chainlit as cl
import uuid
from langgraph.types import Command


async def run_open_deep_research(topic: str, graph, config: dict):
    thread = {"configurable": {"thread_id": str(uuid.uuid4()),
    #    "search_api": "tavily",
        "search_api": "duckduckgo",
        "planner_provider": "openai",
        "planner_model": config["Model"],
        "writer_provider": "openai",
        # "writer_model": config["Model"],
        "writer_model": "gpt-4o",
        "max_search_depth": 1,
    }}
    OUTPUT = ""
    async with cl.Step(name="OpenDeepSearch") as step:
        step.input = {
            'TOOL': 'OpenDeepSearch',
            'TOPIC': topic
        }
        async for event in graph.astream({"topic":topic,}, thread, stream_mode="updates"):
            print("\n\n\n\nEVENT")
            # print(event)
            # print(type(event))
            # if isinstance(event, dict):
            #     print(event.keys())
            
            # step.output = event
            if "__interrupt__" in event.keys():
                intr = event["__interrupt__"][0]
                OUTPUT += f"\n\n\n\n{intr.value}"
                # step.output = intr.value
                isResumable = intr.resumable 
                ns = intr.ns
                when = intr.when
                action_res = await cl.AskActionMessage(
                    content="Pick an action!",
                    actions=[
                        cl.Action(name="continue", payload={"value": "continue"}, label="✅ Continue with plan"),
                        cl.Action(name="cancel", payload={"value": "cancel"}, label="❌ Give input to change plan"),
                    ],
                    timeout=5
                ).send()
                ACTION = None
                if action_res and action_res.get("payload").get("value") == "cancel":
                    suggestions_res = await cl.AskUserMessage(content="What are you suggested changed?", timeout=10).send()
                    if suggestions_res:
                        ACTION = suggestions_res["output"]
                else:
                    ACTION = True

                async for event in graph.astream(
                    Command(resume=ACTION), 
                    thread, 
                    stream_mode="updates"
                ):
                    print(event)
                
                print(f"IsResumable: {isResumable}")
                print(f"Namespace: {ns}")
                print(f"When: {when}")
            else:
                OUTPUT += f"\n\n\n\n{event}"
            
            step.output = OUTPUT

            print("\n\n\n\n")