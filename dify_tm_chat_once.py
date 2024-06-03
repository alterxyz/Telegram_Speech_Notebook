# setted_parameters example: `{'format': 'ex refine', 'memory_context': None, 'topic': None}`

import dify_client as dify
from dify_client import ChatClient

api = "app-"  # Your Dify API key
base_url = "https://api.dify.ai/v1"  # or Your Base URL like http://192.168.50.50/v1
mine = dify.DifyClient(api)
mine.base_url = base_url


def chat_once(setted_parameters: dict, query: str, user_id: str = None) -> str:
    """
    Chat with Dify using the parameters set by the user.

    Args:
        user_id (str): The ID of the user.
        setted_parameter (dict): The parameters set by the user.
        query (str): The query to chat with Dify.
    """
    # Setting the client
    chat_client = ChatClient(api)
    chat_client.base_url = base_url

    chat_response = chat_client.create_chat_message(
        inputs=setted_parameters,
        query=query,
        user="test_user",
        response_mode="blocking",
        conversation_id=None,
    )

    response_data = chat_response.json()
    output = response_data.get("answer", "No response")

    return output


# Example
# setted_parameters = {'format': 'ex refine', 'memory_context': None, 'topic': None}
# query = input("Enter words")
# response = chat_once(setted_parameters, query)
