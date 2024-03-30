import importlib

from krules_core.utils import load_rules_from_rulesdata

m_rules = importlib.import_module("ruleset")
load_rules_from_rulesdata(m_rules.rulesdata)

from celery_app.tasks import *