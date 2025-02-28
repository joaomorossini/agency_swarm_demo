import os
import queue
import threading
from typing_extensions import override

from dotenv import load_dotenv
from openai import AzureOpenAI
from agency_swarm import Agent, Agency, set_openai_client
from agency_swarm.util.streaming import AgencyEventHandler
from agency_swarm.messages import MessageOutput
from openai.types.beta.threads import Message
from openai.types.beta.threads.runs import (
    RunStep,
    ToolCall,
    FunctionToolCall,
    CodeInterpreterToolCall,
    FileSearchToolCall,
)
from agency_swarm.tools import FileSearch, CodeInterpreter

# Import our agents - using the same imports as in demo.ipynb
from agents.NotionProjectAgent import NotionProjectAgent
from agents.TechnicalProjectManager import TechnicalProjectManager
from agents.ResearchAndReportAgent import ResearchAndReportAgent


# Helper functions for file handling (from agency.py)
def get_file_purpose(file_name):
    """Determine the purpose of the file based on its extension."""
    if file_name.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return "vision"
    return "assistants"


def get_tools(file_name):
    """Determine the appropriate tools for the file based on its extension."""
    tools = []

    if file_name.lower().endswith(
        (
            ".py",
            ".js",
            ".html",
            ".css",
            ".ipynb",
            ".r",
            ".c",
            ".cpp",
            ".java",
            ".json",
            ".yaml",
            ".yml",
            ".csv",
            ".tsv",
            ".txt",
        )
    ):
        tools.append({"type": "code_interpreter"})

    if file_name.lower().endswith(
        (
            ".pdf",
            ".docx",
            ".doc",
            ".pptx",
            ".ppt",
            ".xlsx",
            ".xls",
            ".csv",
            ".tsv",
            ".txt",
        )
    ):
        tools.append({"type": "file_search"})

    return tools


# Load environment variables
load_dotenv()


class NotionAgency(Agency):
    """
    Extension of the Agency class that includes a Notion database iframe
    in the Gradio interface.
    """

    def demo_gradio(self, height=450, dark_mode=True, **kwargs):
        """
        Custom implementation of demo_gradio that includes a Notion iframe.
        Inherits most functionality from the parent class but adds an iframe
        at the top of the interface.
        """
        try:
            import gradio as gr
        except ImportError:
            raise Exception("Please install gradio: pip install gradio")

        # Use the Notion embed URL from environment variables
        notion_embed_url = os.getenv("NOTION_DB_URL")

        # Function to generate iframe HTML with timestamp for cache busting
        def generate_iframe_html(ts=None):
            # Add timestamp parameter to force refresh
            url = notion_embed_url
            if ts:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}ts={ts}"

            return f"""
            <div id="iframe-container" style="width: 100%;">
                <iframe src="{url}" width="100%" height="400" frameborder="1" allowfullscreen id="notion-iframe"></iframe>
                <div style="text-align: center; margin-top: 5px; font-size: 12px; color: #888;">
                  If the Notion board doesn't appear, please ensure your Notion page is shared publicly with "Share to web" enabled.
                </div>
            </div>
            """

        js = """function () {
          gradioURL = window.location.href
          if (!gradioURL.endsWith('?__theme={theme}')) {
            window.location.replace(gradioURL + '?__theme={theme}');
          }
        }"""

        # Set dark mode by default
        if dark_mode:
            js = js.replace("{theme}", "dark")
        else:
            js = js.replace("{theme}", "light")

        attachments = []
        images = []
        message_file_names = None
        uploading_files = False
        recipient_agent_names = [agent.name for agent in self.main_recipients]
        recipient_agent = self.main_recipients[0]

        # Track iframe visibility state
        iframe_visible = True

        with gr.Blocks(js=js) as demo:
            chatbot_queue = queue.Queue()

            # Create state for iframe visibility
            iframe_state = gr.State(value=True)

            # Add toggle button and refresh button at the top
            with gr.Row():
                toggle_button = gr.Button(
                    value="Hide Notion Board", elem_id="toggle-button"
                )
                refresh_button = gr.Button(
                    value="Refresh Notion Board", elem_id="refresh-button"
                )

            # Row for iframe with initial HTML
            with gr.Row() as iframe_row:
                iframe = gr.HTML(value=generate_iframe_html())

            # Original components from Agency.demo_gradio
            chatbot = gr.Chatbot(height=height)
            with gr.Row():
                with gr.Column(scale=9):
                    dropdown = gr.Dropdown(
                        label="Recipient Agent",
                        choices=recipient_agent_names,
                        value=recipient_agent.name,
                    )
                    msg = gr.Textbox(label="Your Message", lines=4)
                with gr.Column(scale=1):
                    file_upload = gr.Files(label="OpenAI Files", type="filepath")
            button = gr.Button(value="Send", variant="primary")

            # Function to toggle iframe visibility
            def toggle_iframe(state):
                new_state = not state
                return {
                    iframe_row: gr.update(visible=new_state),
                    toggle_button: (
                        "Show Notion Board" if not new_state else "Hide Notion Board"
                    ),
                    iframe_state: new_state,
                }

            # Function to refresh iframe with timestamp
            def refresh_iframe():
                import time

                # Generate new iframe HTML with current timestamp
                new_html = generate_iframe_html(int(time.time()))
                return gr.update(value=new_html)

            # Connect buttons to functions
            toggle_button.click(
                toggle_iframe,
                inputs=[iframe_state],
                outputs=[iframe_row, toggle_button, iframe_state],
            )

            refresh_button.click(refresh_iframe, outputs=[iframe])

            def handle_dropdown_change(selected_option):
                nonlocal recipient_agent
                recipient_agent = self._get_agent_by_name(selected_option)

            def handle_file_upload(file_list):
                nonlocal attachments
                nonlocal message_file_names
                nonlocal uploading_files
                nonlocal images
                uploading_files = True
                attachments = []
                message_file_names = []
                if file_list:
                    try:
                        for file_obj in file_list:
                            purpose = get_file_purpose(file_obj.name)

                            with open(file_obj.name, "rb") as f:
                                # Upload the file to OpenAI
                                file = self.main_thread.client.files.create(
                                    file=f, purpose=purpose
                                )

                            if purpose == "vision":
                                images.append(
                                    {
                                        "type": "image_file",
                                        "image_file": {"file_id": file.id},
                                    }
                                )
                            else:
                                attachments.append(
                                    {
                                        "file_id": file.id,
                                        "tools": get_tools(file.filename),
                                    }
                                )

                            message_file_names.append(file.filename)
                            print(f"Uploaded file ID: {file.id}")
                        return attachments
                    except Exception as e:
                        print(f"Error: {e}")
                        return str(e)
                    finally:
                        uploading_files = False

                uploading_files = False
                return "No files uploaded"

            def user(user_message, history):
                if not user_message.strip():
                    return user_message, history

                nonlocal message_file_names
                nonlocal uploading_files
                nonlocal images
                nonlocal attachments
                nonlocal recipient_agent

                # Check if attachments contain file search or code interpreter types
                def check_and_add_tools_in_attachments(attachments, recipient_agent):
                    for attachment in attachments:
                        for tool in attachment.get("tools", []):
                            if tool["type"] == "file_search":
                                if not any(
                                    isinstance(t, FileSearch)
                                    for t in recipient_agent.tools
                                ):
                                    # Add FileSearch tool if it does not exist
                                    recipient_agent.tools.append(FileSearch)
                                    recipient_agent.client.beta.assistants.update(
                                        recipient_agent.id,
                                        tools=recipient_agent.get_oai_tools(),
                                    )
                                    print(
                                        "Added FileSearch tool to recipient agent to analyze the file."
                                    )
                            elif tool["type"] == "code_interpreter":
                                if not any(
                                    isinstance(t, CodeInterpreter)
                                    for t in recipient_agent.tools
                                ):
                                    # Add CodeInterpreter tool if it does not exist
                                    recipient_agent.tools.append(CodeInterpreter)
                                    recipient_agent.client.beta.assistants.update(
                                        recipient_agent.id,
                                        tools=recipient_agent.get_oai_tools(),
                                    )
                                    print(
                                        "Added CodeInterpreter tool to recipient agent to analyze the file."
                                    )
                    return None

                check_and_add_tools_in_attachments(attachments, recipient_agent)

                if history is None:
                    history = []

                original_user_message = user_message

                # Append the user message with a placeholder for bot response
                if recipient_agent:
                    user_message = (
                        f"👤 User 🗣️ @{recipient_agent.name}:\n" + user_message.strip()
                    )
                else:
                    user_message = f"👤 User:" + user_message.strip()

                nonlocal message_file_names
                if message_file_names:
                    user_message += "\n\n📎 Files:\n" + "\n".join(message_file_names)

                return original_user_message, history + [[user_message, None]]

            class GradioEventHandler(AgencyEventHandler):
                message_output = None

                @classmethod
                def change_recipient_agent(cls, recipient_agent_name):
                    nonlocal chatbot_queue
                    chatbot_queue.put("[change_recipient_agent]")
                    chatbot_queue.put(recipient_agent_name)

                @override
                def on_message_created(self, message: Message) -> None:
                    if message.role == "user":
                        full_content = ""
                        for content in message.content:
                            if content.type == "image_file":
                                full_content += (
                                    f"🖼️ Image File: {content.image_file.file_id}\n"
                                )
                                continue

                            if content.type == "image_url":
                                full_content += f"\n{content.image_url.url}\n"
                                continue

                            if content.type == "text":
                                full_content += content.text.value + "\n"

                        self.message_output = MessageOutput(
                            "text",
                            self.agent_name,
                            self.recipient_agent_name,
                            full_content,
                        )

                    else:
                        self.message_output = MessageOutput(
                            "text", self.recipient_agent_name, self.agent_name, ""
                        )

                    chatbot_queue.put("[new_message]")
                    chatbot_queue.put(self.message_output.get_formatted_content())

                @override
                def on_text_delta(self, delta, snapshot):
                    chatbot_queue.put(delta.value)

                @override
                def on_tool_call_created(self, tool_call: ToolCall):
                    if isinstance(tool_call, dict):
                        if "type" not in tool_call:
                            tool_call["type"] = "function"

                        if tool_call["type"] == "function":
                            tool_call = FunctionToolCall(**tool_call)
                        elif tool_call["type"] == "code_interpreter":
                            tool_call = CodeInterpreterToolCall(**tool_call)
                        elif (
                            tool_call["type"] == "file_search"
                            or tool_call["type"] == "retrieval"
                        ):
                            tool_call = FileSearchToolCall(**tool_call)
                        else:
                            raise ValueError(
                                "Invalid tool call type: " + tool_call["type"]
                            )

                    # TODO: add support for code interpreter and retrieval tools
                    if tool_call.type == "function":
                        chatbot_queue.put("[new_message]")
                        self.message_output = MessageOutput(
                            "function",
                            self.recipient_agent_name,
                            self.agent_name,
                            str(tool_call.function),
                        )
                        chatbot_queue.put(
                            self.message_output.get_formatted_header() + "\n"
                        )

                @override
                def on_tool_call_done(self, snapshot: ToolCall):
                    if isinstance(snapshot, dict):
                        if "type" not in snapshot:
                            snapshot["type"] = "function"

                        if snapshot["type"] == "function":
                            snapshot = FunctionToolCall(**snapshot)
                        elif snapshot["type"] == "code_interpreter":
                            snapshot = CodeInterpreterToolCall(**snapshot)
                        elif snapshot["type"] == "file_search":
                            snapshot = FileSearchToolCall(**snapshot)
                        else:
                            raise ValueError(
                                "Invalid tool call type: " + snapshot["type"]
                            )

                    self.message_output = None

                    # TODO: add support for code interpreter and retrieval tools
                    if snapshot.type != "function":
                        return

                    chatbot_queue.put(str(snapshot.function))

                    if snapshot.function.name == "SendMessage":
                        try:
                            args = eval(snapshot.function.arguments)
                            recipient = args["recipient"]
                            self.message_output = MessageOutput(
                                "text",
                                self.recipient_agent_name,
                                recipient,
                                args["message"],
                            )

                            chatbot_queue.put("[new_message]")
                            chatbot_queue.put(
                                self.message_output.get_formatted_content()
                            )
                        except Exception as e:
                            pass

                    self.message_output = None

                @override
                def on_run_step_done(self, run_step: RunStep) -> None:
                    if run_step.type == "tool_calls":
                        for tool_call in run_step.step_details.tool_calls:
                            if tool_call.type != "function":
                                continue

                            if tool_call.function.name == "SendMessage":
                                continue

                            self.message_output = None
                            chatbot_queue.put("[new_message]")

                            self.message_output = MessageOutput(
                                "function_output",
                                tool_call.function.name,
                                self.recipient_agent_name,
                                tool_call.function.output,
                            )

                            chatbot_queue.put(
                                self.message_output.get_formatted_header() + "\n"
                            )
                            chatbot_queue.put(tool_call.function.output)

                @override
                @classmethod
                def on_all_streams_end(cls):
                    cls.message_output = None
                    chatbot_queue.put("[end]")

            def bot(original_message, history, dropdown):
                nonlocal attachments
                nonlocal message_file_names
                nonlocal recipient_agent
                nonlocal recipient_agent_names
                nonlocal images
                nonlocal uploading_files

                if not original_message:
                    return (
                        "",
                        history,
                        gr.update(
                            value=recipient_agent.name,
                            choices=set([*recipient_agent_names, recipient_agent.name]),
                        ),
                    )

                if uploading_files:
                    history.append([None, "Uploading files... Please wait."])
                    yield (
                        "",
                        history,
                        gr.update(
                            value=recipient_agent.name,
                            choices=set([*recipient_agent_names, recipient_agent.name]),
                        ),
                    )
                    return (
                        "",
                        history,
                        gr.update(
                            value=recipient_agent.name,
                            choices=set([*recipient_agent_names, recipient_agent.name]),
                        ),
                    )

                print("Message files: ", message_file_names)
                print("Images: ", images)

                if images and len(images) > 0:
                    original_message = [
                        {
                            "type": "text",
                            "text": original_message,
                        },
                        *images,
                    ]

                completion_thread = threading.Thread(
                    target=self.get_completion_stream,
                    args=(
                        original_message,
                        GradioEventHandler,
                        [],
                        recipient_agent,
                        "",
                        attachments,
                        None,
                    ),
                )
                completion_thread.start()

                attachments = []
                message_file_names = []
                images = []
                uploading_files = False

                new_message = True
                while True:
                    try:
                        bot_message = chatbot_queue.get(block=True)

                        if bot_message == "[end]":
                            completion_thread.join()
                            break

                        if bot_message == "[new_message]":
                            new_message = True
                            continue

                        if bot_message == "[change_recipient_agent]":
                            new_agent_name = chatbot_queue.get(block=True)
                            recipient_agent = self._get_agent_by_name(new_agent_name)
                            yield (
                                "",
                                history,
                                gr.update(
                                    value=new_agent_name,
                                    choices=set(
                                        [*recipient_agent_names, recipient_agent.name]
                                    ),
                                ),
                            )
                            continue

                        if new_message:
                            history.append([None, bot_message])
                            new_message = False
                        else:
                            history[-1][1] += bot_message

                        yield (
                            "",
                            history,
                            gr.update(
                                value=recipient_agent.name,
                                choices=set(
                                    [*recipient_agent_names, recipient_agent.name]
                                ),
                            ),
                        )
                    except queue.Empty:
                        break

            button.click(user, inputs=[msg, chatbot], outputs=[msg, chatbot]).then(
                bot, [msg, chatbot, dropdown], [msg, chatbot, dropdown]
            )
            dropdown.change(handle_dropdown_change, dropdown)
            file_upload.change(handle_file_upload, file_upload)
            msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
                bot, [msg, chatbot, dropdown], [msg, chatbot, dropdown]
            )

            # Enable queuing for streaming intermediate outputs
            demo.queue(default_concurrency_limit=10)

        # Launch the demo
        demo.launch(**kwargs)
        return demo


def main():
    print("Setting up the demo...")

    # Configure OpenAI client for agency-swarm
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        timeout=5,
        max_retries=5,
    )

    set_openai_client(client)

    # Create our agents
    technical_project_manager = TechnicalProjectManager()
    research_and_report_agent = ResearchAndReportAgent()
    notion_project_agent = NotionProjectAgent()

    # Create the agency with our agents - using NotionAgency instead of Agency
    agency = NotionAgency(
        agency_chart=[
            technical_project_manager,
            [technical_project_manager, notion_project_agent],
            [technical_project_manager, research_and_report_agent],
        ],
        shared_instructions="agency_manifesto.md",
    )

    # Launch the demo with Gradio's built-in deployment
    return agency.demo_gradio(height=450)


if __name__ == "__main__":
    main()
