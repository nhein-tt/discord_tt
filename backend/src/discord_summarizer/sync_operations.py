# sync_operations.py
import asyncio
import logging
from typing import Dict, List
from .discord_api import fetch_channels, fetch_messages
from .database import DiscordDB
from .sync_manager import SyncStateManager

logger = logging.getLogger(__name__)
db = DiscordDB()

async def sync_channel(channel_id: str, channel_name: str, server_id: str) -> Dict:
    """
    Synchronize messages from a single Discord channel to our database.
    Includes improved error handling and logging.
    """
    result = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "success": False,
        "error": None,
        "messages_synced": 0
    }

    try:
        logger.info(f"Starting sync for channel: {channel_name} ({channel_id})")
        messages = await fetch_messages(channel_id)

        # Store the data in our database
        db.add_channel(channel_id, server_id, channel_name)
        db.add_messages(channel_id, messages)
        db.update_sync_status(channel_id)

        result["success"] = True
        result["messages_synced"] = len(messages)
        logger.info(f"Successfully synced {len(messages)} messages from {channel_name}")

    except PermissionError as e:
        result["error"] = str(e)
        logger.warning(f"Skipping channel {channel_name}: {e}")
    except Exception as e:
        result["error"] = str(e)
        logger.error(f"Error syncing channel {channel_name}: {e}", exc_info=True)

    return result

async def perform_sync(server_id: str, sync_manager: SyncStateManager):
    """
    Performs the complete sync operation for a server, updating the sync state
    as it progresses. Handles channels in batches to manage system resources.
    """
    state = sync_manager.start_sync(server_id)

    try:
        channels = await fetch_channels(server_id)
        sync_manager.update_sync(
            server_id,
            channels_total=len(channels)
        )

        # Process channels in batches of 5
        batch_size = 5
        for i in range(0, len(channels), batch_size):
            channel_batch = channels[i:i + batch_size]
            tasks = []

            for channel in channel_batch:
                if not channel.get("id") or not channel.get("name"):
                    continue

                tasks.append(
                    sync_channel(
                        channel["id"],
                        channel["name"],
                        server_id
                    )
                )

            # Process batch and handle results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    sync_manager.update_sync(
                        server_id,
                        channels_failed=state["channels_failed"] + 1,
                        errors=state["errors"] + [str(result)]
                    )
                elif isinstance(result, dict) and result["success"]:
                    sync_manager.update_sync(
                        server_id,
                        channels_completed=state["channels_completed"] + 1
                    )
                else:
                    sync_manager.update_sync(
                        server_id,
                        channels_failed=state["channels_failed"] + 1,
                        errors=state["errors"] + [result.get("error", "Unknown error")]
                    )

            # Rate limiting between batches
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Sync failed for server {server_id}: {e}", exc_info=True)
        sync_manager.update_sync(
            server_id,
            status="failed",
            error=str(e)
        )

    sync_manager.complete_sync(server_id)
