from typing import List

from krules_core.models import Rule

from strategies.ruleset.common import rulesdata as common_rulesdata

rulesdata: List[Rule] = [] \
                        + common_rulesdata
