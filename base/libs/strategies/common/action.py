import uuid

from krules_core.subject.storaged_subject import Subject

from strategies.strategy import get_subject


def set_action(action: str, reason: str = "shell", subject: Subject = None):
    if subject is None:
        subject = get_subject
    if action in ["Buy", "Sell"]:
        subject.set("action_key", uuid.uuid4().hex, muted=True, use_cache=False)
        subject.set("action_start_reason", reason, muted=True, use_cache=False)
    elif action == "stop":
        subject.set("action_stop_reason", reason, muted=True, use_cache=False)
    else:
        raise ValueError(f"Invalid action: {action}")
    subject.set("action", action, use_cache=False)
    return action


