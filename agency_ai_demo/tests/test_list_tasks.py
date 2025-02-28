import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from agency_swarm import set_openai_client
from agency_swarm import Agent

from agents.ClickUpAgent.tools.ClickUpTools import initialize_clickup_tools

load_dotenv()


def main():
    print("Initializing OpenAI client...")
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        timeout=5,
        max_retries=5,
    )

    set_openai_client(client)

    print("Converting ClickUp tools...")
    clickup_tools = initialize_clickup_tools()

    print("Creating test agent...")
    clickup_agent = Agent(
        name="clickup_agent",
        description="I am a simple agent for testing tools",
        model="gpt-4o",
        tools=clickup_tools,
    )

    print("\nTesting get_tasks_tool...")
    # Test GetTasksTool directly without using the agent
    from agents.ClickUpAgent.tools.ClickUpTools import GetTasksTool

    tool = GetTasksTool()
    result = tool._run(list_id=901307715461)
    print(f"Result from GetTasksTool: {result}")

    print("\nDone!")


if __name__ == "__main__":
    main()
