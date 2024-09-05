from dependency_injector import containers, providers

from app_common.models import Strategy, Symbol


class Container(containers.DeclarativeContainer):
    config = providers.Configuration(strict=True)
    symbol = providers.AbstractFactory(Symbol)
    strategy = providers.AbstractFactory(Strategy)


container = Container()
container.config.from_yaml("./default.yaml")
container.config.from_ini("./config.ini")

container.symbol.override(providers.Factory(Symbol, **container.config.symbol()))

container.strategy.override(providers.Factory(
    Strategy,
    fee=container.config.providers[container.config.symbol().get('provider')].fee(),
    symbol=container.symbol(),
    **container.config.strategy(),
))
