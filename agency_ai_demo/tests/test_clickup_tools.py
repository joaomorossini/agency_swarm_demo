import os
import sys
from dotenv import load_dotenv
import json

# Add the parent directory to sys.path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agency_ai_demo.tools.clickup_tools import (
    CreateTaskTool,
    DeleteTaskTool,
    UpdateTaskTool,
    AddDependencyTool,
    GetListTool,
    GetTasksTool,
    GetTaskTool,
)

# Load environment variables
load_dotenv()


def test_create_task():
    print("\n===== Testing CreateTaskTool =====")
    tool = CreateTaskTool()
    result = tool._run(
        list_id="901307715461",
        name="TEST TASK FROM DIRECT TOOL",
        description="This is a test task created using the CreateTaskTool directly",
        assignees=[81918955],
    )
    print("Result:", result)
    return result


def test_get_tasks():
    print("\n===== Testing GetTasksTool =====")
    tool = GetTasksTool()
    result = tool._run(list_id="901307715461")
    print("Tasks found:", len(result))

    # Print the first task details as an example
    if result and len(result) > 0:
        print("Example task:")
        task = result[0]
        print(f"ID: {task.get('id')}")
        print(f"Name: {task.get('name')}")
        print(f"Status: {task.get('status')}")
        print(f"Assignees: {task.get('assignees')}")

    return result


def test_get_task(task_id=None):
    print("\n===== Testing GetTaskTool =====")
    # If no task_id is provided, get the first task from the list
    if not task_id:
        tasks = test_get_tasks()
        if tasks and len(tasks) > 0:
            task_id = tasks[0].get("id")
            print(f"Using first task ID: {task_id}")

    tool = GetTaskTool()
    result = tool._run(task_id=task_id)
    print("Result:", json.dumps(result, indent=2))
    return result


def test_update_task(task_id=None):
    print("\n===== Testing UpdateTaskTool =====")
    # If no task_id is provided, get the first task from the list
    if not task_id:
        tasks = test_get_tasks()
        if tasks and len(tasks) > 0:
            task_id = tasks[0].get("id")
            print(f"Using first task ID: {task_id}")

    tool = UpdateTaskTool()
    result = tool._run(
        task_id=task_id,
        name="UPDATED TASK NAME",
        description="This task was updated using the UpdateTaskTool directly",
    )
    print("Result:", result)
    return result


def test_add_dependency(task_id=None, depends_on=None):
    print("\n===== Testing AddDependencyTool =====")
    # If no task_ids are provided, get the first two tasks from the list
    if not task_id or not depends_on:
        tasks = test_get_tasks()
        if tasks and len(tasks) >= 2:
            task_id = tasks[0].get("id")
            depends_on = tasks[1].get("id")
            print(f"Using task ID: {task_id}")
            print(f"Using depends_on ID: {depends_on}")

    tool = AddDependencyTool()
    result = tool._run(task_id=task_id, depends_on=depends_on)
    print("Result:", result)
    return result


def test_delete_task(task_id=None):
    print("\n===== Testing DeleteTaskTool =====")
    # If no task_id is provided, create a new task to delete
    if not task_id:
        created_task = test_create_task()
        if isinstance(created_task, dict) and "id" in created_task:
            task_id = created_task["id"]
            print(f"Using newly created task ID: {task_id}")

    tool = DeleteTaskTool()
    result = tool._run(task_id=task_id)
    print("Result:", result)
    return result


def test_get_list():
    print("\n===== Testing GetListTool =====")
    tool = GetListTool()
    result = tool._run(list_id="901307715461")
    print("Result:", json.dumps(result, indent=2))
    return result


def test_all_tools():
    print("Starting ClickUp tools tests...")

    # Step 1: Get all tasks to see what's already there
    tasks = test_get_tasks()

    # Step 2: Create a new task
    created_task = test_create_task()
    if isinstance(created_task, dict) and "id" in created_task:
        new_task_id = created_task.get("id")
        print(f"Created new task with ID: {new_task_id}")

        # Step 3: Get the task details
        test_get_task(new_task_id)

        # Step 4: Update the task
        test_update_task(new_task_id)

        # Step 5: Create another task for dependency testing
        second_task = test_create_task()
        if isinstance(second_task, dict) and "id" in second_task:
            second_task_id = second_task.get("id")
            print(f"Created second task with ID: {second_task_id}")

            # Step 6: Add dependency between tasks
            test_add_dependency(new_task_id, second_task_id)

            # Step 7: Get list details
            test_get_list()

            # Step 8: Delete the tasks we created (cleanup)
            test_delete_task(new_task_id)
            test_delete_task(second_task_id)
        else:
            print("Failed to create second task, skipping dependency test")
    else:
        print("Failed to create task, skipping remaining tests")

    print("\nAll tests completed!")


if __name__ == "__main__":
    test_all_tools()
