import os
from dotenv import load_dotenv
from agency_swarm.tools import BaseTool
from pydantic import Field
from typing import Dict, Any

load_dotenv()

# Load API credentials from environment variables
api_key = os.getenv("EVOLUTION_API_KEY")
api_url = os.getenv("EVOLUTION_API_URL")
api_instance = os.getenv("EVOLUTION_API_INSTANCE")


class SendWhatsAppText(BaseTool):
    """
    Tool for sending WhatsApp text messages to users.
    This tool sends a text message to a specified phone number using the Evolution API.
    Use this when you need to request authorization, feedback, or additional information
    from a human user to make progress on a task or project.
    """

    # Add example_field with a default value to satisfy BaseTool validation
    example_field: str = Field(
        default="whatsapp_text",
        description="Identifier for this tool. Can be left at its default value.",
    )

    phone_number: str = Field(
        ...,
        description="Recipient's phone number in E.164 format (e.g., '5521988456100').",
    )

    message: str = Field(..., description="The text message content to send.")

    def run(self) -> Dict[str, Any]:
        """
        Send a WhatsApp text message to the specified phone number.

        Returns:
            dict: The JSON response from the API containing the message ID on success,
                  or error details on failure.
        """
        import requests

        # Build the complete URL
        instance_name = os.getenv("EVOLUTION_API_INSTANCE", "Cogmo_Secretary_Joao")
        url = f"{os.getenv('EVOLUTION_API_URL')}/message/sendText/{instance_name}"

        # Set up the headers with API key authentication
        headers = {
            "Content-Type": "application/json",
            "apikey": os.getenv("EVOLUTION_API_KEY"),
        }

        # Prepare the request body
        data = {"number": self.phone_number, "text": self.message}

        try:
            # Make the POST request
            response = requests.post(url, headers=headers, json=data)

            # Return the JSON response
            return response.json()
        except Exception as e:
            # Handle any exceptions
            return {
                "error": str(e),
                "status": "failed",
                "message": "Failed to send WhatsApp message",
            }
