from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# load environment variables from .env file
load_dotenv()

openai_key = os.getenv("OPENAI_API_KEY")

llm_name = "gpt-4.1-mini"
model = ChatOpenAI(model_name=llm_name, openai_api_key=openai_key, temperature=0)

message = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is the phtometric stereo?")
]

# res= model.invoke(message)
# print(res)


def first_agent(messagew):
    response = model.invoke(message)
    print(response)
    return response

def run_agent():
    print("Simple AI Agent: Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Exiting the agent. Goodbye!")
            break
        message = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content=user_input)
        ]
        response = first_agent(message)
        print("AI Agent: getting the response..." )
        print(f"AI: {response.content}")
    

if __name__ == "__main__":
    run_agent()

