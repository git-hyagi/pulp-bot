import os
import threading

import llm
import slack

from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter

# load the vars from .env file as env vars
env_path = Path("./.env")
load_dotenv(dotenv_path=env_path)
SLACK_SIGNING_SECRET = os.environ["SLACK_SIGN_SECRET"]
SLACK_TOKEN = os.environ["SLACK_TOKEN"]

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(SLACK_SIGNING_SECRET, "/slack/events", app)
client = slack.WebClient(token=SLACK_TOKEN)
BOT_ID = client.api_call("auth.test")["user_id"]


@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
    channel = event.get("channel")
    user = event.get("user")
    chat_message = event.get("text")

    if BOT_ID != user and chat_message and chat_message.startswith("!pulpbot "):
        parts = chat_message.split(" ", 1)
        prompt = parts[1] if len(parts) > 1 else ""

        client.chat_postMessage(channel=channel, text="Processing question: " + prompt)

        # running the llm in another thread to ack slack event asap
        # if slack don't receive a response in some seconds it will resend the event
        def process_llm():
            answer = llm.run_llm(prompt)
            client.chat_postMessage(channel=channel, text=answer.text)

        threading.Thread(target=process_llm).start()

    return "HTTP 200 OK"


if __name__ == "__main__":
    app.run()
