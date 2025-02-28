import os
from dotenv import load_dotenv
from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, List, Optional, Any, Union

load_dotenv()

notion_integration_secret = os.getenv("NOTION_INTEGRATION_SECRET")
notion_database_id = os.getenv("NOTION_DATABASE_ID")


class CreateTaskTool(BaseTool):
    """
    Tool for creating a new task (page) in a Notion database.
    This tool creates a new page with specified properties and optionally
    adds content blocks to the page.
    """

    # Add example_field with a default value to satisfy BaseTool validation
    example_field: str = Field(
        default="notion_create_task",
        description="Identifier for this tool. Can be left at its default value.",
    )

    title: str = Field(
        ...,
        description="The title of the task (required).",
    )

    status: str = Field(
        default=None,
        description="Status of the task. Options: Backlog, In Progress, In Review, Testing, Completed.",
    )

    priority: str = Field(
        default=None,
        description="Priority of the task. Options: High, Medium, Low.",
    )

    due_date: str = Field(
        default=None,
        description="Due date of the task in YYYY-MM-DD format.",
    )

    assigned_to: List[str] = Field(
        default=None,
        description="List of user IDs to assign the task to.",
    )

    content_blocks: List[Dict[str, Any]] = Field(
        default=None,
        description="List of content blocks to add to the page. See Notion API Block documentation for format.",
    )

    def run(self):
        """
        Create a new task (page) in a Notion database with the specified properties and content.

        Returns:
            dict: The JSON response from the Notion API containing the created page.
        """
        import requests

        # Use the database ID from the parameter or environment variable
        database_id = os.getenv("NOTION_DATABASE_ID")

        # Set up the API endpoint
        url = "https://api.notion.com/v1/pages"

        # Set up the headers
        headers = {
            "Authorization": f"Bearer {os.getenv('NOTION_INTEGRATION_SECRET')}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        # Prepare the request body
        data = {
            "parent": {"type": "database_id", "database_id": database_id},
            "properties": self._build_properties(),
        }

        # Add children blocks if provided
        if self.content_blocks:
            data["children"] = self.content_blocks

        # Make the request
        response = requests.post(url, headers=headers, json=data)

        # Return the JSON response
        return response.json()

    def _build_properties(self) -> Dict[str, Any]:
        """
        Build the properties object based on provided parameters.

        Returns:
            dict: A dictionary containing the page properties in Notion API format.
        """
        properties = {}

        # Title is required
        properties["Task Name"] = {
            "title": [{"type": "text", "text": {"content": self.title}}]
        }

        # Add status if provided
        if self.status:
            properties["Status"] = {"status": {"name": self.status}}

        # Add priority if provided
        if self.priority:
            properties["Priority"] = {"select": {"name": self.priority}}

        # Add due date if provided
        if self.due_date:
            properties["Due Date"] = {"date": {"start": self.due_date}}

        # Add assigned people if provided
        if self.assigned_to:
            properties["Assigned to"] = {
                "people": [{"id": user_id} for user_id in self.assigned_to]
            }

        return properties
