import inspect
from typing import Any, Callable, Dict, List, Optional, Type, Union, get_type_hints
from pydantic import BaseModel, Field, create_model
import functools
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Import the necessary classes
try:
    # For LangChain
    from langchain.tools import BaseTool as LangChainBaseTool
    from langchain.tools.base import ToolException

    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not available. Providing mock classes for documentation.")
    LANGCHAIN_AVAILABLE = False

    class LangChainBaseTool:
        """Mock LangChain BaseTool for documentation"""

        name = "mock_tool"
        description = "Mock tool for documentation"

        def _run(self, *args, **kwargs):
            raise NotImplementedError("This is a mock class")

    class ToolException(Exception):
        """Mock ToolException for documentation"""

        pass


try:
    # For agency-swarm
    from agency_swarm.tools.BaseTool import BaseTool as AgencySwarmBaseTool

    AGENCY_SWARM_AVAILABLE = True
except ImportError:
    logger.warning(
        "Agency Swarm not available. Providing mock classes for documentation."
    )
    AGENCY_SWARM_AVAILABLE = False

    class AgencySwarmBaseTool:
        """Mock Agency Swarm BaseTool for documentation"""

        class ToolConfig:
            strict = True
            one_call_at_a_time = True
            output_as_result = False
            async_mode = None

        def run(self):
            raise NotImplementedError("This is a mock class")


def convert_langchain_tool(
    lc_tool: Union[Type[LangChainBaseTool], Callable]
) -> Type[AgencySwarmBaseTool]:
    """
    Converts a LangChain tool (class-based or function-based) to an agency-swarm compatible tool.

    Args:
        lc_tool: Either a LangChain BaseTool class or a function decorated with @tool

    Returns:
        A new class that inherits from agency_swarm.tools.BaseTool

    Example:
        ```python
        from langchain.tools import BaseTool

        class MyLangChainTool(BaseTool):
            name = "my_tool"
            description = "A sample tool"

            def _run(self, param1: str, param2: int) -> str:
                return f"Processed {param1} and {param2}"

        # Convert to agency-swarm tool
        MyAgencySwarmTool = convert_langchain_tool(MyLangChainTool)

        # Use with agency-swarm
        agent = Agent(
            name="my_agent",
            tools=[MyAgencySwarmTool],  # Pass the class, not an instance
        )
        ```
    """
    if not LANGCHAIN_AVAILABLE or not AGENCY_SWARM_AVAILABLE:
        raise ImportError(
            "Both LangChain and Agency Swarm must be available to convert tools."
        )

    # Check if input is a function (likely decorated with @tool)
    if callable(lc_tool) and not inspect.isclass(lc_tool):
        return _convert_function_tool(lc_tool)

    # If it's a class, ensure it's a subclass of LangChain's BaseTool
    if not issubclass(lc_tool, LangChainBaseTool):
        raise TypeError(f"Expected a LangChain BaseTool subclass, got {lc_tool}")

    # Extract metadata from the LangChain tool
    tool_name = getattr(lc_tool, "name", lc_tool.__name__)
    if tool_name is None:
        tool_name = lc_tool.__name__

    tool_description = getattr(lc_tool, "description", lc_tool.__doc__ or "")

    # Get the schema from the LangChain tool, if any
    schema_cls = getattr(lc_tool, "args_schema", None)

    # Create a new class that inherits from agency_swarm's BaseTool
    class ConvertedTool(AgencySwarmBaseTool):
        """
        Agency Swarm tool converted from LangChain tool.
        """

        # Set up the ToolConfig inner class
        class ToolConfig:
            strict: bool = True
            one_call_at_a_time: bool = True
            output_as_result: bool = False
            async_mode: None = None

        def run(self) -> Dict:
            """
            Execute the tool with runtime validation.
            """
            # Validate required fields based on the original schema
            validation_errors = self._validate_required_fields()
            if validation_errors:
                return {"success": False, "error": validation_errors}

            # Prepare args for the original tool's _run method
            kwargs = {
                field: getattr(self, field)
                for field in self._get_field_names()
                if hasattr(self, field) and getattr(self, field) is not None
            }

            try:
                # Call the original LangChain tool's _run method
                instance = lc_tool()
                result = instance._run(**kwargs)

                # If result is already a dict, return it
                if isinstance(result, dict):
                    return result

                # Otherwise, wrap it in a success response
                return {"success": True, "result": result}
            except ToolException as e:
                # Convert LangChain's exceptions to structured errors
                return {"success": False, "error": str(e)}
            except Exception as e:
                # Handle unexpected errors
                logger.exception(f"Tool execution failed: {str(e)}")
                return {"success": False, "error": f"Tool execution failed: {str(e)}"}

        def _validate_required_fields(self) -> Optional[str]:
            """
            Validate required fields at runtime.
            """
            if not schema_cls:
                return None

            # Try different approaches to identify required fields based on Pydantic version
            missing_fields = []
            try:
                # Attempt to get field info based on Pydantic v1 style
                if hasattr(schema_cls, "__fields__"):
                    for field_name, field_info in schema_cls.__fields__.items():
                        if (
                            field_info.required
                            and getattr(self, field_name, None) is None
                        ):
                            missing_fields.append(field_name)
                # Try Pydantic v2 style
                elif hasattr(schema_cls, "model_fields"):
                    for field_name, field_info in schema_cls.model_fields.items():
                        if (
                            field_info.is_required()
                            and getattr(self, field_name, None) is None
                        ):
                            missing_fields.append(field_name)
                # Fallback to checking for ... (Ellipsis) in class variables
                else:
                    for field_name in schema_cls.__annotations__:
                        class_var = getattr(schema_cls, field_name, None)
                        if class_var is ... and getattr(self, field_name, None) is None:
                            missing_fields.append(field_name)
            except Exception as e:
                logger.warning(f"Error during field validation: {e}")
                # If all else fails, just check for None values
                for field_name in schema_cls.__annotations__:
                    if getattr(self, field_name, None) is None:
                        missing_fields.append(field_name)

            if missing_fields:
                return f"Missing required fields: {', '.join(missing_fields)}"

            return None

        def _get_field_names(self) -> List[str]:
            """
            Get all field names from the schema.
            """
            if schema_cls:
                return list(schema_cls.__annotations__.keys())
            return []

    # Set the tool name and description
    # Use safe string operations for the class name
    safe_name = "".join(
        c for c in tool_name.replace("-", "_") if c.isalnum() or c == "_"
    )
    if safe_name:
        class_name = safe_name[0].upper() + safe_name[1:] + "Converted"
    else:
        class_name = "ConvertedTool"

    ConvertedTool.__name__ = class_name
    ConvertedTool.__doc__ = tool_description

    # Add fields to the converted tool
    if schema_cls:
        _add_fields_from_schema(ConvertedTool, schema_cls)
    else:
        # If no schema_cls, try to infer from _run signature
        _add_fields_from_run_method(ConvertedTool, lc_tool)

    return ConvertedTool


def _add_fields_from_schema(
    target_cls: Type[AgencySwarmBaseTool], schema_cls: Type[BaseModel]
) -> None:
    """
    Add fields from a Pydantic schema to the target class.

    Args:
        target_cls: The class to add fields to
        schema_cls: The Pydantic schema class to extract fields from
    """
    target_cls.__annotations__ = {}

    # Extract field descriptions based on Pydantic version
    field_descriptions = {}
    try:
        if hasattr(schema_cls, "__fields__"):
            # Pydantic v1
            for name, field in schema_cls.__fields__.items():
                field_descriptions[name] = field.field_info.description
        elif hasattr(schema_cls, "model_fields"):
            # Pydantic v2
            for name, field in schema_cls.model_fields.items():
                field_descriptions[name] = field.description
    except Exception as e:
        logger.warning(f"Error extracting field descriptions: {e}")

    # Add each field to the target class
    for field_name, field_type in schema_cls.__annotations__.items():
        description = field_descriptions.get(field_name, f"Parameter: {field_name}")

        # Make the type Optional if it's not already
        if not hasattr(field_type, "__origin__") or field_type.__origin__ is not Union:
            field_type = Optional[field_type]

        # Add the field to the target class with None as default
        setattr(target_cls, field_name, Field(None, description=description))
        target_cls.__annotations__[field_name] = field_type


def _add_fields_from_run_method(
    target_cls: Type[AgencySwarmBaseTool], tool_cls: Type[LangChainBaseTool]
) -> None:
    """
    Add fields inferred from the _run method signature.

    Args:
        target_cls: The class to add fields to
        tool_cls: The LangChain tool class to extract fields from
    """
    target_cls.__annotations__ = {}

    # Get the signature of the _run method
    try:
        # First try to get the _run method from the class
        if hasattr(tool_cls, "_run"):
            run_method = tool_cls._run
        # If that fails, try to get it from an instance
        else:
            instance = tool_cls()
            run_method = instance._run

        signature = inspect.signature(run_method)

        # Skip 'self' parameter if present
        parameters = list(signature.parameters.items())
        if parameters and parameters[0][0] == "self":
            parameters = parameters[1:]

        for param_name, param in parameters:
            # Skip *args and **kwargs
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            # Get the type annotation if available
            param_type = (
                param.annotation if param.annotation != inspect.Parameter.empty else Any
            )

            # Make the type Optional
            optional_type = Optional[param_type]

            # Add the field to the target class
            setattr(
                target_cls,
                param_name,
                Field(None, description=f"Parameter: {param_name}"),
            )
            target_cls.__annotations__[param_name] = optional_type

    except Exception as e:
        logger.warning(f"Error extracting fields from _run method: {e}")


def _convert_function_tool(tool_func: Callable) -> Type[AgencySwarmBaseTool]:
    """
    Convert a function-based tool (decorated with @tool) to an agency-swarm compatible tool.

    Args:
        tool_func: A function decorated with @tool

    Returns:
        A new class that inherits from agency_swarm.tools.BaseTool
    """
    # Extract metadata from the function
    # Handle case where tool_func might be a StructuredTool instead of a direct function
    if hasattr(tool_func, "name"):
        tool_name = tool_func.name
    else:
        tool_name = getattr(tool_func, "__name__", "function_tool")

    tool_description = getattr(
        tool_func, "description", getattr(tool_func, "__doc__", "") or ""
    )

    # Get the signature of the underlying function
    if hasattr(tool_func, "_run"):
        func_to_inspect = tool_func._run
    elif hasattr(tool_func, "func"):
        func_to_inspect = tool_func.func
    else:
        func_to_inspect = tool_func

    signature = inspect.signature(func_to_inspect)

    # Create a new class that inherits from agency_swarm's BaseTool
    class ConvertedFunctionTool(AgencySwarmBaseTool):
        """
        Agency Swarm tool converted from a LangChain function tool.
        """

        # Set up the ToolConfig inner class
        class ToolConfig:
            strict: bool = True
            one_call_at_a_time: bool = True
            output_as_result: bool = False
            async_mode: None = None

        def run(self) -> Dict:
            """
            Execute the tool with runtime validation.
            """
            # Prepare args for the original function
            kwargs = {
                param_name: getattr(self, param_name, None)
                for param_name in signature.parameters
                if hasattr(self, param_name) and getattr(self, param_name) is not None
            }

            # Validate required parameters
            missing_params = []
            for param_name, param in signature.parameters.items():
                if (
                    param.default == inspect.Parameter.empty  # No default value
                    and kwargs.get(param_name) is None  # Not provided
                ):
                    missing_params.append(param_name)

            if missing_params:
                return {
                    "success": False,
                    "error": f"Missing required parameters: {', '.join(missing_params)}",
                }

            try:
                # Call the original function or tool
                if hasattr(tool_func, "_run"):
                    result = tool_func._run(**kwargs)
                elif hasattr(tool_func, "__call__"):
                    result = tool_func(**kwargs)
                else:
                    result = func_to_inspect(**kwargs)

                # If result is already a dict, return it
                if isinstance(result, dict):
                    return result

                # Otherwise, wrap it in a success response
                return {"success": True, "result": result}
            except Exception as e:
                # Handle errors
                logger.exception(f"Tool execution failed: {str(e)}")
                return {"success": False, "error": f"Tool execution failed: {str(e)}"}

    # Set the tool name and description
    # Use safe string operations for the class name
    safe_name = "".join(
        c for c in tool_name.replace("-", "_") if c.isalnum() or c == "_"
    )
    if safe_name:
        class_name = safe_name[0].upper() + safe_name[1:] + "Tool"
    else:
        class_name = "ConvertedFunctionTool"

    ConvertedFunctionTool.__name__ = class_name
    ConvertedFunctionTool.__doc__ = tool_description

    # Set up annotations dictionary
    ConvertedFunctionTool.__annotations__ = {}

    # Add fields based on function parameters
    for param_name, param in signature.parameters.items():
        # Get the type annotation if available
        param_type = (
            param.annotation if param.annotation != inspect.Parameter.empty else Any
        )

        # Make it Optional
        optional_type = Optional[param_type]

        # Get description from docstring if available
        param_description = f"Parameter: {param_name}"

        # Add the field to the class
        setattr(
            ConvertedFunctionTool,
            param_name,
            Field(None, description=param_description),
        )
        ConvertedFunctionTool.__annotations__[param_name] = optional_type

    return ConvertedFunctionTool


# Batch conversion helper
def convert_langchain_tools(
    lc_tools: List[Union[Type[LangChainBaseTool], Callable]]
) -> List[Type[AgencySwarmBaseTool]]:
    """
    Convert multiple LangChain tools to agency-swarm compatible tools.

    Args:
        lc_tools: A list of LangChain BaseTool classes or functions decorated with @tool

    Returns:
        A list of converted agency-swarm tool classes
    """
    converted_tools = []
    for tool in lc_tools:
        try:
            converted_tool = convert_langchain_tool(tool)
            converted_tools.append(converted_tool)
        except Exception as e:
            logger.error(
                f"Failed to convert tool {getattr(tool, 'name', getattr(tool, '__name__', 'unknown'))}: {e}"
            )

    return converted_tools
