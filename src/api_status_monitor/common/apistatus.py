"""The API status information model.

This module is shared by the producer and consumer.
"""

import logging
import json
from datetime import datetime


class APIStatusInformation():

    def __init__(self, site, endpoint, status_code, log, error,
                 response_time_ms, sla_ms, timestamp=None):
        assert site is not None
        assert endpoint is not None
        self.site = site
        self.endpoint = endpoint
        self.status_code = status_code
        self.log = log
        self.error = error
        self.response_time_ms = response_time_ms
        self.sla_ms = sla_ms
        if not timestamp:
            # Create UTC timestamp, millis are enough
            self.timestamp = int(datetime.utcnow().timestamp())
        else:
            self.timestamp = timestamp

    def success(self):
        return not self.error and \
            (self.status_code > 199 and self.status_code < 300)

    def in_sla(self):
        return self.response_time_ms <= self.sla_ms

    def to_json(self):
        return json.dumps({
            "site": self.site,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "log": self.log,
            "error": self.error,
            "response_time_ms": self.response_time_ms,
            "sla_ms": self.sla_ms,
            "in_sla": self.in_sla(),
            "timestamp": self.timestamp,
            }).encode("utf-8")

    @classmethod
    def from_json(cls, data):
        try:
            json_obj = json.loads(data)
            return APIStatusInformation(
                json_obj.get("site"),
                json_obj.get("endpoint"),
                json_obj.get("status_code"),
                json_obj.get("log"),
                json_obj.get("error"),
                json_obj.get("response_time_ms"),
                json_obj.get("sla_ms"),
                json_obj.get("timestamp")
            )
        except json.JSONDecodeError:
            logging.warning("JSON parse error.")
            return None
