import os
import sys
import requests
from dotenv import load_dotenv
from langchain.tools import BaseTool
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.tools import ToolException
from typing import Any, Type
import re
from composio.tools.local.clickup.actions.get_task import (
    GetTask,
    GetTaskRequest,
    GetTaskResponse,
)

# Add the parent directory to sys.path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add project utils
from utils.tool_wrapper import convert_langchain_tools
from utils.ensure_serializable import ensure_serializable

load_dotenv()


CLICKUP_TOKEN = os.getenv("CLICKUP_TOKEN")


# TODO: FIX THIS TOOL
class GetTaskTool(BaseTool):
    name: str = "get_task_tool"
    description: str = """
    Ferramenta para visualizar detalhes de uma tarefa no ClickUp.
    - Obter detalhes da tarefa:
        Invocar: "GetTaskTool" com o ID da tarefa e parâmetros opcionais.
    """
    args_schema: Type[BaseModel] = GetTaskRequest
    headers: dict = {"Authorization": f"{CLICKUP_TOKEN}"}

    def _init_(self, **data):
        super()._init_(**data)

    def _run(self, **kwargs) -> Any:
        """Executa a requisição para obter detalhes de uma tarefa no ClickUp"""

        action = GetTask()

        url = f"{action.url}{action.path}".format(task_id=kwargs.get("task_id"))

        query_params = {k: v for k, v in kwargs.items() if v is not None}

        response = requests.get(url, headers=self.headers, params=query_params)

        if response.status_code == 200:
            response_json = response.json()
        else:
            try:
                response_json = response.json()
            except requests.JSONDecodeError:
                response_json = {"error": "Invalid JSON response"}

        response = GetTaskResponse(data=response_json)

        filtered_response = {
            "id": response.data.get("id"),
            "name": response.data.get("name"),
            "status": response.data.get("status", {}).get("status"),
            "due_date": response.data.get("due_date"),
            "date_created": response.data.get("date_created"),
            "url": response.data.get("url"),
            "assignees": [
                {"id": assignee.get("id"), "username": assignee.get("username")}
                for assignee in response.data.get("assignees", [])
            ],
            "error": response.data.get("error"),
        }

        return filtered_response
