import uuid

from strategy_common.ioc import container

strategy = container.strategy()


# DEPRECATED
def set_action(action: str, reason: str = "shell"):
    subject = strategy.get_subject()
    if action in ["Buy", "Sell"]:
        subject.set("action_key", uuid.uuid4().hex, muted=True, use_cache=False)
        subject.set("action_start_reason", reason, muted=True, use_cache=False)
    elif action == "stop":
        subject.set("action_stop_reason", reason, muted=True, use_cache=False)
    elif action == "ready":
        subject.set("action_ready_reason", reason, muted=True, use_cache=False)
    else:
        raise ValueError(f"Invalid action: {action}")
    subject.set("action", action, use_cache=False)
    return action
