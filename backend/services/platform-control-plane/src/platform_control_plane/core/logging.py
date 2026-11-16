import json
import logging
from datetime import UTC, datetime


def log_event(event: str, correlation_id: str) -> None:
    # Only fixed event names and server-generated IDs are logged; never format exceptions.
    logging.getLogger("platform_control_plane").info(
        json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "INFO",
                "service": "platform-control-plane",
                "correlation_id": correlation_id,
                "event": event,
            }
        )
    )
