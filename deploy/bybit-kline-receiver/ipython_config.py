import krules_env
krules_env.init()


c.InteractiveShellApp.exec_lines = [
    'from krules_core.providers import subject_factory',
    # 'from krules_core.providers import configs_factory',
    'from krules_core.providers import event_router_factory',
    'router = event_router_factory()',
    # 'from django.apps import apps',
    # 'from django.conf import settings',
    # 'apps.populate(settings.INSTALLED_APPS)',
    # 'from superbot.strategy import strategy_verb',
    # '_verb = lambda s, v: strategy_verb(s, "manual", v, True)',
    # 'from superbot.price import tune_price',
    # 'from django_superbot.models import *',
    # 'from krules_djangoapps_procevents.models import ProcessingEvent',
    # 'from krules_djangoapps_scheduler.models import ScheduledEvent',
    # 'from app_logger.models import ActionLog',
    # 'sol=subject_factory("bybit:symbol:solusdt", use_cache_default=False)',
    # 'bnb=subject_factory("bybit:symbol:bnbusdt", use_cache_default=False)',
    # 'eth=subject_factory("bybit:symbol:ethusdt", use_cache_default=False)',
    # 'btc=subject_factory("bybit:symbol:btcusdt", use_cache_default=False)',
    # 'atom=subject_factory("bybit:symbol:atomusdt", use_cache_default=False)',
    # '_all=[sol, bnb, eth, btc, atom]',
    # '_verb=lambda s, v: strategy_verb(s, "manual", v)',
    # '_none=lambda s: strategy_verb(s, "manual", None, True)',
    #'from ishell import *',
]
