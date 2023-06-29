import requests

from state import state


def get_resources():
    url = f"{state.NI_PREFIX}{state.NI_IP}/resources/"
    response = requests.get(url)
    return response.json()


if __name__ == "__main__":
    print(get_resources())
