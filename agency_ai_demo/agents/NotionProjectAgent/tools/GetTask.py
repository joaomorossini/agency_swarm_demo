import os
from dotenv import load_dotenv
from agency_swarm.tools import BaseTool
from pydantic import Field

load_dotenv()

notion_integration_secret = os.getenv("NOTION_INTEGRATION_SECRET")


class GetTaskTool(BaseTool):
    """
    Tool for retrieving a specific task (page) from Notion.
    This tool fetches all properties of a specific task using its page ID.
    Note that page content (blocks) is not retrieved, only the page properties.
    """

    # Add example_field with a default value to satisfy BaseTool validation
    example_field: str = Field(
        default="notion_task",
        description="Identifier for this tool. Can be left at its default value.",
    )

    page_id: str = Field(
        ...,
        description="The ID of the Notion page (task) to retrieve. This is a required field.",
    )

    def run(self):
        """
        Retrieve a Notion page (task) by its ID.

        Returns:
            dict: The JSON response from the Notion API containing the page properties.
        """
        import requests

        # Set up the API endpoint
        url = f"https://api.notion.com/v1/pages/{self.page_id}"

        # Set up the headers
        headers = {
            "Authorization": f"Bearer {os.getenv('NOTION_INTEGRATION_SECRET')}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        # Make the request
        response = requests.get(url, headers=headers)

        # Return the JSON response
        return response.json()
