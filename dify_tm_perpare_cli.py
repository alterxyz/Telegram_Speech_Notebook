import dify_client as dify
import json
from datetime import datetime


def init_api(api_key, base_url):
    response = mine.get_application_parameters("user").json()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = {
        "api_key": api_key,
        "base_url": base_url,
        "timestamp": timestamp,
        "response": response,
    }
    api_info = api + ".json"
    try:
        with open(api_info, "r") as file:
            summary_data = json.load(file)
    except FileNotFoundError:
        summary_data = []
    summary_data.append(result)
    with open(api_info, "w") as file:
        json.dump(summary_data, file, indent=4)


def init_parameters(api, base_url):
    # Get the parameters need from the api_info, only load "user_input_form", just load the last one
    init_api(api, base_url)
    api_info = api + ".json"
    with open(api_info, "r") as file:
        summary_data = json.load(file)
        parameters = summary_data[-1]["response"]["user_input_form"]
        # Access the first element of the list
        return parameters


def cli_set_application_parameters(api, base_url):
    parameters = init_parameters(api, base_url)
    setted_parameters = {}

    for param in parameters:
        input_type, details = next(iter(param.items()))
        prompt = f"{details['label']}"

        if input_type == "select":
            options_str = "\n".join(details["options"])
            prompt += f":\nType exactly one of the following options:\n{options_str}\n"

        while True:

            if "required" in details and not details["required"]:
                print("\n[Optional field, press Enter to skip.]")
            user_input = input(f"\n[{prompt}]\n> Your choice: ")
            if "required" in details and not details["required"] and user_input == "":
                setted_parameters[details["variable"]] = None
                break

            if input_type == "select" and user_input in details["options"]:
                setted_parameters[details["variable"]] = user_input
                break

            elif input_type == "text-input" or input_type == "paragraph":
                setted_parameters[details["variable"]] = user_input
                break

            elif input_type == "number":
                try:
                    user_input = int(user_input)
                    setted_parameters[details["variable"]] = user_input
                    break
                except ValueError:
                    print("[Error, try again]")
            else:
                print("[Error, try again]")
    return setted_parameters


def dify_select_param(detail):
    options = []
    options.append(detail["label"])
    for option in detail["options"]:
        options.append(option)
    return options


if __name__ == "__main__":
    api = "app-"  # Your Dify API key
    base_url = "https://api.dify.ai/v1"

    print(f"Welcome to Dify parameters setter CLI")
    # Base URL
    print(f"Current base_url is {base_url}")
    new_base_url = input("Enter new base_url or press Enter to continue: ")
    if new_base_url != "":
        base_url = new_base_url

    # API
    if api == "app-":

        api = input(f"----------------------\nEnter your Dify API key: ")

    print(api)
    mine = dify.DifyClient(api)
    mine.base_url = base_url
    print(f"----------------------\nYou raw API data is :\n----------------------\n")
    print(
        f"{init_parameters(api, base_url)}\n----------------------\nYour API info stored as {api}.json\nDo not share the file or date in it.\n----------------------\n"
    )

    # Set parameters
    setted_parameters = cli_set_application_parameters(api, base_url)
    print(f"\n----------------------\nYour Setted_parameters(or 'inputs'):\n")
    # Print the setted parameters so copy and paste it anywhere needed
    print(setted_parameters)
