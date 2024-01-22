from krules_core.base_functions.processing import ProcessingFunction

from krules_companion_client.http import CompanionClient

cm_client = CompanionClient()


def _guess_entity_and_group_from_subject(subject_name):
    if subject_name.startswith('symbol:'):
        _, provider, category, symbol = subject_name.split(':')
        return symbol.upper(), f"symbols.{provider}.{category}"


class CompanionPublish(ProcessingFunction):

    def execute(self, entity=None, group=None, properties=None):

        if entity is None and group is None:
            entity, group = _guess_entity_and_group_from_subject(self.subject.name)

        if properties is None:
            properties = {}

        cm_client.publish(
            entity=entity,
            group=group,
            properties=properties,
        )
