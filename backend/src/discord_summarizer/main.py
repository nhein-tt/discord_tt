from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .discord_api import scrape_messages, fetch_channels, filter_recent_messages, fetch_messages, summarize_channel
from .summarizer import summarize_discord_data
import os
import logging
import asyncio
from datetime import datetime, timezone
from .database import DiscordDB
app = FastAPI(root_path="/api")
db = DiscordDB()

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def sync_single_channel(channel_id: str, channel_name: str, server_id: str):
    """
    Synchronizes a single Discord channel's messages with our database.
    This function handles the actual sync process for one channel.
    """
    try:
        # First, record the channel in our database
        db.add_channel(channel_id, server_id, channel_name)

        # Fetch messages from Discord
        messages = await fetch_messages(channel_id)  # Make sure fetch_messages is async

        # Store them in our database
        db.add_messages(channel_id, messages)

        # Update the sync timestamp
        db.update_sync_status(channel_id)

        logging.info(f"Successfully synced channel {channel_name}")
        return True
    except Exception as e:
        logging.error(f"Error syncing channel {channel_name}: {str(e)}")
        return False

@app.get("/")
async def root():
    return {"message": "Hello, World!"}

@app.post("/clear-cache/{server_id}")
async def clear_summaries_cache(server_id: str):
    """
    Clears cached summaries for all channels in a server.
    """
    try:
        with db.get_db() as conn:
            # Delete all cached summaries for channels in this server
            conn.execute("""
                DELETE FROM channel_summaries
                WHERE channel_id IN (
                    SELECT channel_id FROM channels
                    WHERE server_id = ?
                )
            """, (server_id,))

        return {
            "status": "success",
            "message": "Cache cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/summarize/{server_id}")
async def get_summary(server_id: str):
    """
    Generates summaries for all channels in a server using cached data.
    This version implements a two-level caching strategy:
    1. Channel-level caching: Individual channel summaries are cached
    2. Message-level efficiency: Only processes messages that aren't in the current cache
    """
    try:
        channels = db.get_server_channels(server_id)

        if not channels:
            return {
                "server_id": server_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "channels": {},
                "total_channels_analyzed": 0,
                "active_channels": 0,
                "sync_status": "No cached data available. Please run /sync first."
            }

        channel_summaries = {}
        cache_hits = 0
        cache_misses = 0

        for channel in channels:
            channel_name = channel["name"]
            channel_id = channel["channel_id"]

            try:
                # First, try to get a cached summary
                cached_summary = db.get_cached_summary(channel_id)

                if cached_summary:
                    # Use the cached summary
                    channel_summaries[channel_name] = {
                        "summary": cached_summary["summary"],
                        "message_count": cached_summary["message_count"],
                        "last_active": cached_summary["last_active"],
                        "total_participants": cached_summary["total_participants"],
                        "cache_status": "hit",
                        "generated_at": cached_summary["generated_at"]
                    }
                    cache_hits += 1
                else:
                    # No valid cachE, need to generate a new summary
                    recent_messages = db.get_recent_messages(channel_id)

                    if recent_messages:
                        # Generate new summary
                        summary = summarize_channel(recent_messages, channel_name)

                        if summary:
                            last_active = max(
                                datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00'))
                                for msg in recent_messages
                            )

                            summary_data = {
                                "summary": summary,
                                "message_count": len(recent_messages),
                                "last_active": last_active.isoformat(),
                                "total_participants": len(set(msg["author"] for msg in recent_messages)),
                                "cache_status": "miss",
                                "generated_at": datetime.now(timezone.utc).isoformat()
                            }

                            # Cache the new summary
                            db.cache_summary(channel_id, summary_data)

                            channel_summaries[channel_name] = summary_data
                            cache_misses += 1

            except Exception as e:
                logging.error(f"Error processing channel {channel_name}: {str(e)}")
                continue

        current_time = datetime.now(timezone.utc)

        return {
            "server_id": server_id,
            "timestamp": current_time.isoformat(),
            "channels": channel_summaries,
            "total_channels_analyzed": len(channels),
            "active_channels": len(channel_summaries),
            "cache_metrics": {
                "hits": cache_hits,
                "misses": cache_misses,
                "hit_ratio": cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0
            }
        }

    except Exception as e:
        logging.error(f"Error in get_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# @app.get("/summarize/{server_id}")
# async def get_summary(server_id: str):
#     """
#     Generates summaries for all channels in a server using only cached data.
#     This route never calls the Discord API directly.
#     """
#     try:
#         # Get channels from our database instead of Discord
#         channels = db.get_server_channels(server_id)

#         if not channels:
#             return {
#                 "server_id": server_id,
#                 "timestamp": datetime.now(timezone.utc).isoformat(),
#                 "channels": {},
#                 "total_channels_analyzed": 0,
#                 "active_channels": 0,
#                 "sync_status": "No cached data available. Please run /sync first."
#             }

#         channel_summaries = {}
#         oldest_sync = None

#         for channel in channels:
#             channel_name = channel["name"]
#             channel_id = channel["channel_id"]
#             last_synced = channel["last_synced"]

#             # Keep track of oldest sync time for metadata
#             if last_synced:
#                 oldest_sync = min(oldest_sync or last_synced, last_synced)

#             try:
#                 # Get messages from our database
#                 recent_messages = db.get_recent_messages(channel_id)

#                 if recent_messages:
#                     summary = summarize_channel(recent_messages, channel_name)

#                     if summary:
#                         last_active = max(
#                             datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00'))
#                             for msg in recent_messages
#                         )

#                         channel_summaries[channel_name] = {
#                             "summary": summary,
#                             "message_count": len(recent_messages),
#                             "last_active": last_active.isoformat(),
#                             "total_participants": len(set(msg["author"] for msg in recent_messages)),
#                             "last_synced": last_synced
#                         }

#             except Exception as e:
#                 logging.error(f"Error processing channel {channel_name}: {str(e)}")
#                 continue

#         # Calculate sync staleness for the response
#         current_time = datetime.now(timezone.utc)
#         sync_age = None
#         if oldest_sync:
#             oldest_sync_dt = datetime.fromisoformat(oldest_sync)
#             if oldest_sync_dt.tzinfo is None:
#                     # If the datetime is naive, assume it's in UTC and make it aware
#                 oldest_sync_dt = oldest_sync_dt.replace(tzinfo=timezone.utc)
#             sync_age = (current_time - oldest_sync_dt).total_seconds() / 3600

#         return {
#             "server_id": server_id,
#             "timestamp": current_time.isoformat(),
#             "channels": channel_summaries,
#             "total_channels_analyzed": len(channels),
#             "active_channels": len(channel_summaries),
#             "data_freshness": {
#                 "oldest_sync": oldest_sync,
#                 "sync_age_hours": round(sync_age, 1) if sync_age is not None else None,
#                 "sync_status": "up_to_date" if sync_age and sync_age < 1 else "stale"
#             }
#         }

#     except Exception as e:
#         logging.error(f"Error in get_summary: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/sync/{server_id}")
async def force_sync(server_id: str):
    """
    Endpoint to force a full resync of all channels in a server.
    Now properly handles async operations.
    """
    try:
        channels = await fetch_channels(server_id)  # Make sure fetch_channels is async
        synced_channels = 0
        failed_channels = 0

        # Create a list of sync tasks
        sync_tasks = []
        for channel in channels:
            if not channel.get("name") or not channel.get("channel_id"):
                continue

            sync_tasks.append(
                sync_single_channel(
                    channel["channel_id"],
                    channel["name"],
                    server_id
                )
            )

        # Run all sync tasks concurrently and collect results
        results = await asyncio.gather(*sync_tasks, return_exceptions=True)

        # Count successes and failures
        for result in results:
            if isinstance(result, Exception):
                failed_channels += 1
            elif result:  # Successfully synced
                synced_channels += 1
            else:  # Sync returned False
                failed_channels += 1

        return {
            "status": "completed",
            "synced_channels": synced_channels,
            "failed_channels": failed_channels,
            "total_channels": len(channels)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.get("/summarize/{server_id}")
# async def get_summary(server_id: str):
#     """
#     Endpoint that fetches, filters, and summarizes Discord messages by channel.
#     Returns channel-specific summaries for messages from the past week.
#     """
#     try:
#         channels = fetch_channels(server_id)
#         channel_summaries = {}

#         for channel in channels:
#             channel_name = channel["name"]
#             channel_id = channel["id"]

#             try:
#                 # Fetch all messages first
#                 all_messages = fetch_messages(channel_id)

#                 # Filter to recent messages only
#                 recent_messages = filter_recent_messages(all_messages)

#                 if recent_messages:  # Only process channels with recent activity
#                     summary = summarize_channel(recent_messages, channel_name)
#                     if summary:
#                         # Ensure we're working with UTC-aware datetimes
#                         last_active = max(
#                             datetime.fromisoformat(msg["timestamp"].replace('Z', '+00:00'))
#                             for msg in recent_messages
#                         )

#                         channel_summaries[channel_name] = {
#                             "summary": summary,
#                             "message_count": len(recent_messages),
#                             "last_active": last_active.isoformat(),
#                             "total_participants": len(set(msg["author"] for msg in recent_messages))
#                         }
#             except PermissionError:
#                 logging.warning(f"Skipping channel {channel_name} due to permissions")
#             except Exception as e:
#                 logging.error(f"Error processing channel {channel_name}: {str(e)}")
#                 continue

#         return {
#             "server_id": server_id,
#             "timestamp": datetime.now(timezone.utc).isoformat(),
#             "channels": channel_summaries,
#             "total_channels_analyzed": len(channels),
#             "active_channels": len(channel_summaries)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # @app.get("/summarize/{server_id}")
# # async def get_summary(server_id: str):
# #     try:
# #         discord_data = scrape_messages(server_id)
# #         summary = summarize_discord_data(discord_data)
# #         return {"server_id": server_id, "summary": summary}
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))
