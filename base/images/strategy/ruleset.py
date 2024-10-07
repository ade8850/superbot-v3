from typing import List

from krules_core.models import Rule

from strategy_common.ruleset import rulesdata as common_rulesdata

rulesdata: List[Rule] = [] \
                        + common_rulesdata
