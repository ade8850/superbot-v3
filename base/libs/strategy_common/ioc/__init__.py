from dependency_injector import containers, providers

from strategy_common.models import Strategy, Symbol


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(strict=True)
    symbol = providers.AbstractSingleton(Symbol)
    strategy = providers.AbstractSingleton(Strategy)


container = Container()
container.config.from_yaml("./default.yaml")
container.config.from_ini("./config.ini")

container.symbol.override(providers.Singleton(Symbol, **container.config.symbol()))

container.strategy.override(providers.Singleton(
    Strategy,
    fee=container.config.providers[container.config.symbol().get('provider')].fee(),
    symbol=container.symbol(),
    **container.config.strategy(),
))
