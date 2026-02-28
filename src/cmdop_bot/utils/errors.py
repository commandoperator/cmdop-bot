"""User-friendly error messages for gRPC / CMDOP errors."""


def friendly_error(e: str | Exception) -> str:
    """Convert exception or error string to a user-friendly message."""
    msg = str(e)

    if "session_id" in msg or "No active session" in msg or ("not found" in msg.lower() and "session" in msg.lower()):
        return "Machine is offline or CMDOP agent is not running.\nhttps://cmdop.com/downloads/"

    if "context canceled" in msg or "CANCELLED" in msg:
        return "Request was interrupted. Please try again."

    if "DEADLINE_EXCEEDED" in msg or "timeout" in msg.lower():
        return "Request timed out. The task may be too complex — try a simpler prompt."

    if "UNAVAILABLE" in msg or "Connection refused" in msg:
        return "Server unavailable. Check your connection and try again."

    if "workspace" in msg.lower() and "different" in msg.lower():
        return f"Wrong workspace: {msg}"

    return msg
