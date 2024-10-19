c.InteractiveShellApp.exec_lines = [
    'import krules_env',
    'krules_env.init()',
    'from krules_core.providers import subject_factory',
    'from krules_core.providers import event_router_factory',
    'from strategy_common import set_action',
    'router = event_router_factory()',
    'from strategy_common.ioc import container',
    'strategy = container.strategy()',
    'ss = strategy.get_subject()',
    'sym = strategy.symbol.get_subject()',
    'imp = container.implementation()',
]