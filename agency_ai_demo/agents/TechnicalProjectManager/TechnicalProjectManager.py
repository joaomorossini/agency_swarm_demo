from agency_swarm.agents import Agent


class TechnicalProjectManager(Agent):
    def __init__(self):
        super().__init__(
            name="TechnicalProjectManager",
            description="João Morossini's AI proxy, working as a Technical Project Manager at Agency AI",
            instructions="./instructions.md",
            files_folder="./files",
            schemas_folder="./schemas",
            tools=[],
            tools_folder="./tools",
            temperature=0.3,
            max_prompt_tokens=25000,
        )

    def response_validator(self, message):
        return message
