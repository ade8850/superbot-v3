c.InteractiveShellApp.exec_lines = [
    'import krules_env',
    'krules_env.init()',
    'from krules_core.providers import subject_factory',
    'from krules_core.providers import configs_factory',
    'from krules_core.providers import event_router_factory',
    'from strategies.strategy import get_subject',
    'from strategies.limit_price import set_limit_price',
    'from strategies.common import set_verb',
    'strategy = get_subject()',
    'router = event_router_factory()',
]