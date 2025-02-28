import os

from agency_swarm.agents import Agent
from .tools.GetTasks import GetTasksTool
from .tools.GetTask import GetTaskTool
from .tools.CreateTask import CreateTaskTool


class NotionProjectAgent(Agent):
    def __init__(self):
        # Retrieve the Notion integration secret from the environment
        try:
            integration_secret = os.environ["NOTION_INTEGRATION_SECRET"]
        except KeyError:
            raise EnvironmentError(
                "NOTION_INTEGRATION_SECRET environment variable is not set."
            )

        # Initialize the parent Agent class with updated parameters
        super().__init__(
            name="NotionProjectAgent",
            description="Project Management Assistant who tracks and updates project progress on Notion",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[GetTasksTool, GetTaskTool, CreateTaskTool],
            tools_folder="./tools",
            model="gpt-4o",
            temperature=0.3,
            max_prompt_tokens=25000,
            # api_headers={
            #     "notion_tasks.json": {
            #         "Authorization": f"Bearer {integration_secret}",
            #         "Notion-Version": "2022-06-28",
            #     }
            # },
        )

    def response_validator(self, message):
        return message
