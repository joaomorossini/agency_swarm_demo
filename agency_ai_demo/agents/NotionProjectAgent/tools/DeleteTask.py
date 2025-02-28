import os
from dotenv import load_dotenv
from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, Any

load_dotenv()

notion_integration_secret = os.getenv("NOTION_INTEGRATION_SECRET")


class DeleteTaskTool(BaseTool):
    """
    Tool for deleting (archiving) a task (page) in Notion.
    In Notion, deleting a page is done by archiving it.
    This tool archives the specified page, making it disappear from its parent database.
    """

    # Add example_field with a default value to satisfy BaseTool validation
    example_field: str = Field(
        default="notion_delete_task",
        description="Identifier for this tool. Can be left at its default value.",
    )

    page_id: str = Field(
        ...,
        description="The ID of the Notion page (task) to delete/archive. This is a required field.",
    )

    def run(self) -> Dict[str, Any]:
        """
        Delete (archive) a Notion page (task) with the specified ID.

        Returns:
            dict: The JSON response from the Notion API confirming the page has been archived.
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

        # Prepare the request body - to archive a page, set 'archived' to true
        data = {"archived": True}

        # Make the request (PATCH method for updates, including archiving)
        response = requests.patch(url, headers=headers, json=data)

        # Return the JSON response
        return response.json()
