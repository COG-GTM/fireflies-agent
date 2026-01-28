from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])
anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

TARGET_CHANNEL_NAME = os.environ.get("TARGET_CHANNEL_NAME", "granola-mena-apac")
TARGET_CHANNEL_ID = os.environ.get("TARGET_CHANNEL_ID")

def get_channel_id_by_name(client, channel_name):
    """Get channel ID by channel name"""
    try:
        result = client.conversations_list(types="public_channel,private_channel")
        for channel in result["channels"]:
            if channel["name"] == channel_name:
                return channel["id"]
    except Exception as e:
        print(f"Error fetching channel ID: {e}")
    return None

@app.event("message")
def handle_message(event, say, client):
    global TARGET_CHANNEL_ID

    
    if TARGET_CHANNEL_ID is None:
        TARGET_CHANNEL_ID = get_channel_id_by_name(client, TARGET_CHANNEL_NAME)
        if TARGET_CHANNEL_ID is None:
            print(f"Warning: Channel '{TARGET_CHANNEL_NAME}' not found")
            return
    
    event_channel = event.get("channel")
    
    if event_channel != TARGET_CHANNEL_ID:
        print(f"[DEBUG] Ignoring message from different channel")
        return
    
    if event.get("bot_id") or event.get("subtype"):
        print(f"[DEBUG] Ignoring bot message or subtype: bot_id={event.get('bot_id')}, subtype={event.get('subtype')}")
        return
    
    message_text = event.get("text", "")
    thread_ts = event.get("ts")
    channel_id = event["channel"]
    
    print(f"Processing message from {TARGET_CHANNEL_NAME}: {message_text[:100]}...")
    
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        text="✅ Message received! Processing meeting notes..."
    )

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    print(f"⚡️ Slack bot is running! Listening to channel: {TARGET_CHANNEL_NAME}")
    handler.start()