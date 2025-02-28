import os
from dotenv import load_dotenv
from agency_swarm.tools import BaseTool
from pydantic import Field

load_dotenv()

notion_integration_secret = os.getenv("NOTION_INTEGRATION_SECRET")
notion_database_id = os.getenv("NOTION_DATABASE_ID")


class GetTasksTool(BaseTool):
    """
    Tool for retrieving tasks from a Notion database.
    This tool allows querying tasks with optional filtering and sorting capabilities
    based on properties like Due Date, Status, Priority, and Task Name.
    """

    # Add example_field with a default value to satisfy BaseTool validation
    example_field: str = Field(
        default="notion_tasks",
        description="Identifier for this tool. Can be left at its default value.",
    )

    status: str = Field(
        default=None,
        description="Filter tasks by status. Options: Backlog, In Progress, In Review, Testing, Completed.",
    )

    priority: str = Field(
        default=None,
        description="Filter tasks by priority. Options: High, Medium, Low.",
    )

    due_date_before: str = Field(
        default=None,
        description="Filter tasks due before this date (format: YYYY-MM-DD).",
    )

    due_date_after: str = Field(
        default=None,
        description="Filter tasks due after this date (format: YYYY-MM-DD).",
    )

    sort_by: str = Field(
        default="Due Date",
        description="Property to sort by. Options: Due Date, Status, Priority, Task Name.",
    )

    sort_direction: str = Field(
        default="ascending",
        description="Sort direction. Options: ascending, descending.",
    )

    def run(self):
        """
        Query a Notion database for tasks with optional filtering and sorting.

        Returns:
            dict: The JSON response from the Notion API containing the tasks.
        """
        import requests

        # Use the database ID from the environment variable
        database_id = os.getenv("NOTION_DATABASE_ID")

        # Set up the API endpoint
        url = f"https://api.notion.com/v1/databases/{database_id}/query"

        # Set up the headers
        headers = {
            "Authorization": f"Bearer {os.getenv('NOTION_INTEGRATION_SECRET')}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        # Prepare the request body
        data = {}

        # Build filter
        filters = []

        if self.status:
            filters.append({"property": "Status", "status": {"equals": self.status}})

        if self.priority:
            filters.append(
                {"property": "Priority", "select": {"equals": self.priority}}
            )

        if self.due_date_before:
            filters.append(
                {"property": "Due Date", "date": {"before": self.due_date_before}}
            )

        if self.due_date_after:
            filters.append(
                {"property": "Due Date", "date": {"after": self.due_date_after}}
            )

        if filters:
            if len(filters) > 1:
                data["filter"] = {"and": filters}
            else:
                data["filter"] = filters[0]

        # Add sorting
        if self.sort_by:
            data["sorts"] = [
                {"property": self.sort_by, "direction": self.sort_direction}
            ]

        # Make the request
        response = requests.post(url, headers=headers, json=data)

        # Return the JSON response
        return response.json()
