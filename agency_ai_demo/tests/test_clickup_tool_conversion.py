import os
import sys
import inspect
import logging
from typing import List, Type, Any, Callable, Dict, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the tool wrapper
from utils.tool_wrapper import convert_langchain_tool, LangChainBaseTool

# Import all tools from the clickup_tools module
from tools.clickup_tools import (
    CreateTaskTool,
    DeleteTaskTool,
    UpdateTaskTool,
    CreateTaskCommentTool,
    GetTaskCommentsTool,
    AddTaskToListTool,
    RemoveTaskFromListTool,
    CreateFolderlessListTool,
    GetListsTool,
    AddDependencyTool,
    GetAuthorizedTeamsWorkspacesTool,
    GetAuthorizedUserTool,
    GetFolderTool,
    GetFoldersTool,
    GetListTool,
    GetListMembersTool,
    GetTaskMembersTool,
    GetSpaceTool,
    GetSpacesTool,
    GetFilteredTeamTasksTool,
    GetTasksTool,
    GetTaskTool,
    GetWorkspaceSeatsTool,
    date_to_timestamp,
)


def test_tool_conversion():
    """
    Test the conversion of all ClickUp tools to agency-swarm compatible tools.
    """
    # Define all tools to test explicitly
    class_tools = [
        CreateTaskTool,
        DeleteTaskTool,
        UpdateTaskTool,
        CreateTaskCommentTool,
        GetTaskCommentsTool,
        AddTaskToListTool,
        RemoveTaskFromListTool,
        CreateFolderlessListTool,
        GetListsTool,
        AddDependencyTool,
        GetAuthorizedTeamsWorkspacesTool,
        GetAuthorizedUserTool,
        GetFolderTool,
        GetFoldersTool,
        GetListTool,
        GetListMembersTool,
        GetTaskMembersTool,
        GetSpaceTool,
        GetSpacesTool,
        GetFilteredTeamTasksTool,
        GetTasksTool,
        GetTaskTool,
        GetWorkspaceSeatsTool,
    ]

    function_tools = [date_to_timestamp]

    logger.info(
        f"Testing {len(class_tools)} class-based tools and {len(function_tools)} function-based tools"
    )

    # Test conversion of class-based tools
    successful_conversions = []
    failed_conversions = []

    # Convert and test each class-based tool
    for tool_cls in class_tools:
        tool_name = tool_cls.__name__
        try:
            logger.info(f"Converting {tool_name}...")
            converted_tool = convert_langchain_tool(tool_cls)
            successful_conversions.append((tool_name, converted_tool))
            logger.info(f"✅ Successfully converted {tool_name}")
        except Exception as e:
            logger.error(f"❌ Failed to convert {tool_name}: {e}")
            failed_conversions.append((tool_name, str(e)))

    # Convert and test each function-based tool
    for tool_func in function_tools:
        # For function tools, use the function's name directly
        if hasattr(tool_func, "__name__"):
            tool_name = tool_func.__name__
        else:
            tool_name = "function_tool"

        try:
            logger.info(f"Converting {tool_name}...")
            converted_tool = convert_langchain_tool(tool_func)
            successful_conversions.append((tool_name, converted_tool))
            logger.info(f"✅ Successfully converted {tool_name}")
        except Exception as e:
            logger.error(f"❌ Failed to convert {tool_name}: {e}")
            failed_conversions.append((tool_name, str(e)))

    # Print summary report
    print("\n" + "=" * 50)
    print("CONVERSION SUMMARY REPORT")
    print("=" * 50)
    print(f"Total tools tested: {len(class_tools) + len(function_tools)}")
    print(f"Successfully converted: {len(successful_conversions)}")
    print(f"Failed conversions: {len(failed_conversions)}")

    if successful_conversions:
        print("\n" + "-" * 25)
        print("SUCCESSFULLY CONVERTED TOOLS:")
        print("-" * 25)
        for name, _ in successful_conversions:
            print(f"✅ {name}")

    if failed_conversions:
        print("\n" + "-" * 25)
        print("FAILED CONVERSIONS:")
        print("-" * 25)
        for name, error in failed_conversions:
            print(f"❌ {name}: {error}")

    return successful_conversions, failed_conversions


if __name__ == "__main__":
    successful_tools, failed_tools = test_tool_conversion()

    # Exit with non-zero code if any conversions failed
    sys.exit(1 if failed_tools else 0)
