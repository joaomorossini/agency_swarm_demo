from agency_swarm.agents import Agent


class ResearchAndReportAgent(Agent):
    def __init__(self):
        super().__init__(
            name="ResearchAndReportAgent",
            description="Project Management Assistant who supports project planning and execution by performing researching, writing reports and sending them via e-mail or text",
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
