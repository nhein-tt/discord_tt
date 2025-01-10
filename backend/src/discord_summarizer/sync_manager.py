# sync_manager.py
from typing import Dict, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class SyncStateManager:
    """
    Manages the state of Discord channel synchronization operations.
    This class keeps track of all active sync operations and their progress.
    """
    def __init__(self):
        # Dictionary to store active sync operations, keyed by server ID
        self.active_syncs: Dict[str, Dict] = {}

    def start_sync(self, server_id: str) -> Dict:
        """
        Initialize a new sync operation for a server. If a sync is already
        running for this server, returns the existing sync state.
        """
        if server_id in self.active_syncs:
            return self.active_syncs[server_id]

        sync_state = {
            "server_id": server_id,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "in_progress",
            "channels_total": 0,
            "channels_completed": 0,
            "channels_failed": 0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "errors": []
        }
        self.active_syncs[server_id] = sync_state
        return sync_state

    def update_sync(self, server_id: str, **kwargs) -> None:
        """
        Update the sync state with new information. The kwargs can include
        any fields that should be updated in the sync state.
        """
        if server_id in self.active_syncs:
            self.active_syncs[server_id].update(kwargs)
            self.active_syncs[server_id]["last_updated"] = datetime.now(timezone.utc).isoformat()

    def complete_sync(self, server_id: str) -> None:
        """
        Mark a sync operation as complete and record the end time.
        """
        if server_id in self.active_syncs:
            self.active_syncs[server_id]["status"] = "completed"
            self.active_syncs[server_id]["end_time"] = datetime.now(timezone.utc).isoformat()

    def get_sync_state(self, server_id: str) -> Optional[Dict]:
        """
        Get the current state of a sync operation for a given server.
        Returns None if no sync operation exists for the server.
        """
        return self.active_syncs.get(server_id)
