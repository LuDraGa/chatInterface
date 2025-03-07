import chainlit as cl
from openai import AsyncOpenAI, OpenAI
import os
from dotenv import load_dotenv
import yaml
from typing import Optional

# Load environment variables
load_dotenv()

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
    with open("user_credentials.yaml", "r") as file:
        data = yaml.safe_load(file)
    # Iterate over the user list
    for user in data.get("users", []):
        if user["username"] == username and user["password"] == password:
            return cl.User(
                identifier=username, metadata={"role": user["role"], "provider": "yaml"}
            )
    return None

@cl.on_chat_start
async def start():
    await cl.Message(content="Let's start the personality test?").send()

@cl.on_message
async def main(message: cl.Message):
    test_one_prompt = """
    The test should have the following characteristics: :  
        I want the test to be modeled after the work of Dr. Robert McCrae, a renowned psychologist known for his expertise 
        in personality assessment.The scenarios should be designed to elicit responses that provide insight into the user's 
        personality traits and tendencies.
        You should not ask for more than 5 scenarios, all should have multiple options.
        Additionally, I want the AI assistant to use these inputs and provide an accurate assessment of 
        their personality at the very end of the test by giving a score on a scale from 1 to 100 for the following categories.
        categories = ['Neuroticism', 'Extraversion', 'Conscientiousness', 'Agreeableness', 'Openness']
    . 
    Start the test now, one scenario at a time
    """
    test_two_prompt = """
    Myers Briggs Personality Test
    <Test format>
    </Test format>
    <Information source>
    </Information source>
    <Results format>
    </Results format>
    """
    test_three_prompt = """
    Enneagram Personality Test
    <Test format>
    </Test format>
    <Information source>
    </Information source>
    <Results format>
    </Results format>
    """
    test_four_prompt = """
    Big Five Personality Test
    <Test format>
    </Test format>
    <Information source>
    </Information source>
    <Results format>
    </Results format>
    """
    try:
        response = await client.chat.completions.create(
            # model="gpt-4o",  
            model="gpt-4ox",  #changed to fail till rest of the code is written
            messages=[
                {
                    "content": test_one_prompt,
                    "role": "system"
                },
                {
                    "content": "Let's start the test",
                    "role": "user"
                },
                {
                    "content": message.content,
                    "role": "user"
                }
            ],
            temperature=0.7,
        )
        print(response)
        await cl.Message(content=response.choices[0].message.content).send()
    except Exception as e:
        print(f"Error: {str(e)}")
        await cl.Message(content=f"An error occurred: {str(e)}").send()

if __name__ == "__main__":
    cl.run()

