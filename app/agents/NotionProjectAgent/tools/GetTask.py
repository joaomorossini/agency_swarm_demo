import os
from dotenv import load_dotenv
from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, List, Optional, Any

load_dotenv()

notion_integration_secret = os.getenv("NOTION_INTEGRATION_SECRET")


class GetTaskTool(BaseTool):
    """
    Tool for retrieving a specific task (page) from Notion.
    This tool fetches the properties of a specific task using its page ID and
    by default, does not fetch the page content (blocks). Content can be included by setting include_content to True.
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

    include_content: bool = Field(
        default=False,
        description="Whether to include the page content (blocks) in the response. When True, all nested blocks will be included.",
    )

    page_size: int = Field(
        default=100,
        description="Number of blocks to retrieve per request. Maximum is 100.",
    )

    def run(self):
        """
        Retrieve a Notion page (task) by its ID, optionally including its content.

        Returns:
            dict: A dictionary containing the page properties and optionally its content.
        """
        import requests

        result = {}

        # Fetch page properties
        properties = self._get_page_properties()
        result["properties"] = properties

        # Fetch page content if requested
        if self.include_content:
            content = self._get_page_content()
            result["content"] = content

        return result

    def _get_page_properties(self) -> Dict[str, Any]:
        """
        Retrieve the properties of a Notion page.

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

        return response.json()

    def _get_page_content(self) -> List[Dict[str, Any]]:
        """
        Retrieve the content (blocks) of a Notion page including all nested blocks.

        Returns:
            list: A list of block objects representing the page content.
        """
        import requests

        # Since pages are also blocks, we can use the page ID as a block ID
        blocks = []
        has_more = True
        start_cursor = None

        # Set up the headers
        headers = {
            "Authorization": f"Bearer {os.getenv('NOTION_INTEGRATION_SECRET')}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        # Paginate through all blocks
        while has_more:
            # Build URL with pagination parameters
            url = f"https://api.notion.com/v1/blocks/{self.page_id}/children?page_size={self.page_size}"
            if start_cursor:
                url += f"&start_cursor={start_cursor}"

            # Make the request
            response = requests.get(url, headers=headers)
            data = response.json()

            # Add blocks to our result
            if "results" in data:
                current_blocks = data["results"]

                # Always fetch children of blocks with children
                for i, block in enumerate(current_blocks):
                    if block.get("has_children", False):
                        current_blocks[i]["children"] = self._get_block_children(
                            block["id"]
                        )

                blocks.extend(current_blocks)

            # Update pagination info
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        return blocks

    def _get_block_children(self, block_id: str) -> List[Dict[str, Any]]:
        """
        Recursively retrieve children of a block.

        Args:
            block_id: The ID of the block to retrieve children for.

        Returns:
            list: A list of block objects representing the block's children.
        """
        import requests

        # Set up the headers
        headers = {
            "Authorization": f"Bearer {os.getenv('NOTION_INTEGRATION_SECRET')}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        # Build URL
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size={self.page_size}"

        # Make the request
        response = requests.get(url, headers=headers)
        data = response.json()

        blocks = []
        if "results" in data:
            blocks = data["results"]

            # Recursively fetch children
            for i, block in enumerate(blocks):
                if block.get("has_children", False):
                    blocks[i]["children"] = self._get_block_children(block["id"])

        return blocks
