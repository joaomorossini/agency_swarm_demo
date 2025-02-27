import os
import sys
import json
import traceback
from dotenv import load_dotenv
from openai import AzureOpenAI
from agency_swarm import set_openai_client, Agent, Agency

from tools.clickup_tools import initialize_clickup_tools, GetTasksTool, GetTaskTool

load_dotenv()


def main():
    try:
        print("Initializing OpenAI client...")
        client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            timeout=10,
            max_retries=5,
        )

        set_openai_client(client)

        # First test the tool directly
        print("\n==== Testing GetTasksTool directly ====")
        tool = GetTasksTool()
        result = tool._run(list_id=901307715461)
        print(f"Direct result: {json.dumps(result, indent=2)}")

        print("\n==== Testing GetTaskTool directly ====")
        get_task_tool = GetTaskTool()
        task_id = "86a700c6e"
        direct_result = get_task_tool._run(task_id=task_id)
        print(f"Direct result: {json.dumps(direct_result, indent=2)}")

        # Now test through Agency Swarm
        print("\n==== Testing through Agency Swarm ====")

        # Convert tools
        print("Converting ClickUp tools...")
        clickup_tools = initialize_clickup_tools()

        # Instructions
        clickup_instructions = """
        You need to use the get_tasks_tool to retrieve tasks from list_id 901307715461.
        Always show the full output to the user.
        """

        print("Creating ClickUp agent...")
        clickup_agent = Agent(
            name="clickup_agent",
            description="I help with ClickUp tasks",
            instructions=clickup_instructions,
            model="gpt-4o",
            tools=clickup_tools,
        )

        # Create the agency with a single agent
        print("Creating agency...")
        agency = Agency(
            agency_chart=[
                clickup_agent,
            ]
        )

        # Run the query through the agency
        print("\nSending query to agent...")
        user_query = "Use the get_tasks_tool to get all tasks in list_id 901307715461 and show me the complete results without summarizing."
        print(f"Query: '{user_query}'")

        response = agency.get_completion(user_query)
        print(f"\nAgent response: {response}")

        print("\nDone!")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("\nTraceback:")
        traceback.print_exception(*sys.exc_info())


if __name__ == "__main__":
    main()
