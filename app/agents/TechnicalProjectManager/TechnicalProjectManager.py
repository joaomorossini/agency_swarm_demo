from agency_swarm.agents import Agent
from .tools.SendWhatsAppText import SendWhatsAppText
from .tools.CreateTask import CreateTask
from .tools.UpdateTask import UpdateTask
from .tools.DeleteTask import DeleteTask
from .tools.GetTask import GetTask
from .tools.GetTasks import GetTasks


class TechnicalProjectManager(Agent):
    def __init__(self):
        super().__init__(
            name="TechnicalProjectManager",
            description="João Morossini's AI proxy, working as a Technical Project Manager at VRSEN AI",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[
                SendWhatsAppText,
                CreateTask,
                UpdateTask,
                DeleteTask,
                GetTask,
                GetTasks,
            ],
            tools_folder="./tools",
            model="gpt-4o",
            temperature=0.3,
            max_prompt_tokens=25000,
        )

    def response_validator(self, message):
        return message
