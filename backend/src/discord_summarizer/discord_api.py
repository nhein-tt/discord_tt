import logging
import aiohttp
from .config import DISCORD_TOKEN, DISCORD_API_BASE
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from .summarizer import call_openai_api

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "Authorization": DISCORD_TOKEN,
    "Content-Type": "application/json"
}

async def fetch_channels(server_id: str) -> List[Dict]:
    """
    Asynchronously fetches channel list from Discord API.
    """
    url = f"{DISCORD_API_BASE}/guilds/{server_id}/channels"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            if response.status == 403:
                raise PermissionError(f"Access denied for server ID: {server_id}")
            response.raise_for_status()
            return await response.json()

async def fetch_messages(channel_id: str) -> List[Dict]:
    """
    Asynchronously fetches messages from a Discord channel.
    """
    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            if response.status == 403:
                raise PermissionError(f"Access denied for channel ID: {channel_id}")
            response.raise_for_status()
            return await response.json()

def filter_recent_messages(messages: List[Dict], days: int = 7) -> List[Dict]:
    """
    Filters messages to only include those from the last specified number of days.
    This function handles the filtering that we previously tried to do at the API level.

    Args:
        messages: List of message dictionaries with timestamp information
        days: Number of days to look back (default is 7)

    Returns:
        List of filtered messages from the specified time period
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    return [
        msg for msg in messages
        if datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00')) > cutoff_date
    ]


# def fetch_messages(channel_id: str) -> List[Dict]:
#     url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
#     # Get messages from the last week
#     week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
#     params = {"after": week_ago}

#     response = requests.get(url, headers=HEADERS, params=params)
#     if response.status_code == 403:
#         raise PermissionError(f"Access denied for channel ID: {channel_id}")
#     response.raise_for_status()

#     return [
#         {
#             "author": msg["author"]["username"],
#             "content": msg["content"],
#             "timestamp": msg["timestamp"]
#         }
#         for msg in response.json()
#     ]

def summarize_channel(messages: List[Dict], channel_name: str) -> Optional[str]:
    """
    Creates a summary of messages from a specific channel.
    Returns None if there are no messages to summarize.
    """
    if not messages:
        return None

    # Group messages by day to provide better context for the summary
    message_text = "\n".join([
        f"{msg['author']}: {msg['content']}"
        for msg in messages
    ])

    prompt = f"""Analyze the following messages from Discord channel '{channel_name}'
    and provide a concise summary of the key discussions from the past week. Focus on:

    1. Main conversation topics and themes
    2. Important questions or issues raised
    3. Any significant announcements or decisions
    4. Notable community interactions or discussions

    Channel: #{channel_name}
    Messages:
    {message_text[:3000]}  # Limiting context window for API
    """

    try:
        response = call_openai_api(prompt)
        return response
    except Exception as e:
        logging.error(f"Failed to summarize channel {channel_name}: {e}")
        return f"Error summarizing channel: {str(e)}"

# def summarize_channel(messages: List[Dict], channel_name: str) -> Optional[str]:
#     if not messages:
#         return None

#     message_text = "\n".join([
#         f"{msg['author']}: {msg['content']}"
#         for msg in messages
#     ])

#     prompt = f"""Summarize the key discussions and topics from the following Discord channel '{channel_name}' messages from the past week.
#     Focus on:
#     1. Main topics discussed
#     2. Key questions or issues raised
#     3. Any decisions or conclusions reached

#     Messages:
#     {message_text[:3000]}  # Limiting context window
#     """

#     try:
#         response = call_openai_api(prompt)
#         return response
#     except Exception as e:
#         logging.error(f"Failed to summarize channel {channel_name}: {e}")
#         return f"Error summarizing channel: {str(e)}"
# def fetch_messages(channel_id):
#     url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
#     response = requests.get(url, headers=HEADERS)
#     if response.status_code == 403:
#         raise PermissionError(f"Access denied for channel ID: {channel_id}")
#     response.raise_for_status()
#     return [
#         {"author": msg["author"]["username"], "content": msg["content"]}
#         for msg in response.json()
#     ]

def scrape_messages(server_id):
    try:
        channels = fetch_channels(server_id)
    except Exception as e:
        logger.error(f"Failed to fetch channels for server {server_id}: {e}")
        raise  # Re-raise to handle server-level issues upstream

    scraped_data = {}

    for channel in channels:
        channel_name = channel["name"]
        channel_id = channel["id"]
        try:
            logger.info(f"Fetching messages for channel: {channel_name}")
            messages = fetch_messages(channel_id)
            scraped_data[channel_name] = messages
        except PermissionError as e:
            logger.warning(f"Skipping channel {channel_name} due to permission error: {e}")
        except Exception as e:
            logger.error(f"Failed to fetch messages for channel {channel_name}: {e}")

    return scraped_data
