import os

from krules_core.base_functions.processing import *
from krules_core.models import Rule

import google.cloud.logging
client = google.cloud.logging.Client(project=os.environ["PROJECT_ID"])
logger = client.logger(os.environ['LOGGER_NAME'])

from pprint import pprint


rulesdata: List[Rule] = [
    Rule(
        name="send-procevent-to-gcp-logger",
        processing=[
            Process(lambda payload: payload.pop("_event_info")),
            Process(
                lambda payload: (
                    logger.log_struct(
                        payload,
                        severity=payload["got_errors"] and "ERROR" or "INFO",
                        labels={
                            "krules.dev/app": "procevent-logger-publisher",
                            "krules.dev/project": os.environ["PROJECT_NAME"],
                            "krules.dev/target": os.environ["TARGET"]
                        }
                    )
                )
            )
        ]
    ),
    Rule(
        name="pprint",
        processing=[
            Process(
                lambda payload: (
                    pprint(payload)
                )
            )
        ]
    )

]
