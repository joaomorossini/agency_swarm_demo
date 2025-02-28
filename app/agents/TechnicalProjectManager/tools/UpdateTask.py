import os
from dotenv import load_dotenv
from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, List, Optional, Any, Union

load_dotenv()

notion_integration_secret = os.getenv("NOTION_INTEGRATION_SECRET")


class UpdateTaskTool(BaseTool):
    """
    Tool for updating an existing task (page) in Notion.
    This tool allows modifying task properties such as title, status, priority, due date, and assignments.
    Note that this tool only updates properties, not the content blocks of the page.
    """

    # Add example_field with a default value to satisfy BaseTool validation
    example_field: str = Field(
        default="notion_update_task",
        description="Identifier for this tool. Can be left at its default value.",
    )

    page_id: str = Field(
        ...,
        description="The ID of the Notion page (task) to update. This is a required field.",
    )

    title: str = Field(
        default=None,
        description="The new title of the task.",
    )

    task_description: str = Field(
        default=None,
        description="The new text description of the task.",
    )

    status: str = Field(
        default=None,
        description="New status of the task. Options: Backlog, In Progress, Testing, Completed.",
    )

    priority: str = Field(
        default=None,
        description="New priority of the task. Options: High, Medium, Low.",
    )

    due_date: str = Field(
        default=None,
        description="New due date of the task in YYYY-MM-DD format. Use 'null' to remove the date.",
    )

    def run(self):
        """
        Update an existing Notion page (task) with the specified properties.

        Returns:
            dict: The JSON response from the Notion API containing the updated page.
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

        # Prepare the request body
        data = {"properties": self._build_properties()}

        # Make the request (PATCH method for updates)
        response = requests.patch(url, headers=headers, json=data)

        # Return the JSON response
        return response.json()

    def _build_properties(self) -> Dict[str, Any]:
        """
        Build the properties object based on provided parameters.
        Only includes properties that were specified for update.

        Returns:
            dict: A dictionary containing the page properties to update in Notion API format.
        """
        properties = {}

        # Add title if provided
        if self.title is not None:
            properties["Task Name"] = {
                "title": [{"type": "text", "text": {"content": self.title}}]
            }

        # Add task description if provided
        if self.task_description is not None:
            properties["Task Description"] = {
                "rich_text": [
                    {"type": "text", "text": {"content": self.task_description}}
                ]
            }

        # Add status if provided
        if self.status is not None:
            properties["Status"] = {"status": {"name": self.status}}

        # Add priority if provided
        if self.priority is not None:
            properties["Priority"] = {"select": {"name": self.priority}}

        # Add due date if provided
        if self.due_date is not None:
            # Check if we're clearing the date
            if self.due_date.lower() == "null":
                properties["Due Date"] = {"date": None}
            else:
                properties["Due Date"] = {"date": {"start": self.due_date}}

        # Add assigned people if provided
        # if self.assigned_to is not None:
        #     properties["Assigned to"] = {
        #         "people": [{"id": user_id} for user_id in self.assigned_to]
        #     }

        return properties
