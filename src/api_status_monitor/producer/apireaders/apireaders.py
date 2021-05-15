"""Web site endpoint readers
"""

import asyncio.exceptions
import html
import json
import logging
import re
import time

import jsonpath_ng
import aiohttp
from api_status_monitor.common.apistatus import APIStatusInformation


class InvalidReaderTypeException(Exception):
    pass


def create_reader(**kwargs):
    """Create API reader from keyword arguments.
    Kwargs (common):
      name (str): Reader name
      type (str): json|regex to select type of the created reader.
      sla_ms (int): The request SLA timeout.
      site: (str): The target site URL.
      endpoint (str, default: /): The target API endpoint.

    Kwargs (JSON API Reader):
      json_path (str): A jsonpath expression to read single field and value
                       to collect as a log from the request.

    Kwargs (Regex Reader):
      regex (str): Python regular expression to match a single group to
                   collect as a log from the request.
    """
    reader_type = kwargs.pop("type")
    if "regex" == reader_type:
        return RegexReader(**kwargs)
    elif "json" == reader_type:
        return JSONAPIReader(**kwargs)
    else:
        raise InvalidReaderTypeException("Invalid reader type.")


class LogExtractionException(Exception):
    pass


class APIReader():
    """The base class for different API and web page readers.
    The request and response time calculation is done here
    and the APIStatusInformation object created and populated.

    The read implementation is asynchronous and asyncio event loop
    expected to run the
    read.
    """

    def __init__(self, name, sla_ms, site, endpoint=None):
        """
        Args:
            sla_timeout_ms (int): The SLA timeout in milliseconds.
            site (str): The target site address.
        """
        # Divide the millliseconds to float of seconds.
        self._name = name
        self._sla_ms = sla_ms
        self._sla_secs = sla_ms / 1000
        self._site = site
        self._endpoint = endpoint if endpoint else "/"

    def url(self):
        return "{site}{endpoint}".format(site=self._site, endpoint=self._endpoint)

    async def read(self):
        """Asynchronous API read request.

        Returns:
            APIStatusInformation: The result object.
        """
        async with aiohttp.ClientSession() as client:
            start = time.perf_counter()
            try:
                async with client.get(self.url(),
                                      timeout=self._sla_secs) \
                                      as response:
                    elapsed = int((time.perf_counter() - start) * 1000)

                    log = ""
                    error = ""
                    try:
                        log = self.extract_data(await response.text())
                    except LogExtractionException as ex:
                        error = str(ex)
                    return APIStatusInformation(self._site, self._endpoint,
                                                response.status, log,
                                                error, elapsed,
                                                self._sla_ms)
            except asyncio.exceptions.TimeoutError:
                # Millisecond precision is enough.
                elapsed = int((time.perf_counter() - start) * 1000)
                logging.info("(%s) API '%s' reading failed on timeout of '%s' ms.",
                             self._name, self.url(), self._sla_ms)
                return APIStatusInformation(self._site, self._endpoint,
                                            0, "", "TIMEOUT", elapsed,
                                            self._sla_ms)
            except Exception as ex:
                # Millisecond precision is enough.
                elapsed = int((time.perf_counter() - start) * 1000)
                logging.error("(%s) API '%s' reading failed on exception.",
                             self._name, self.url(), exc_info=1)
                return APIStatusInformation(self._site, self._endpoint,
                                            0, "", str(ex), elapsed,
                                            self._sla_ms)


class JSONAPIReader(APIReader):

    def __init__(self, name, sla_ms, site, endpoint, json_path):
        """
        Args:
            sla_ms (int): The SLA timeout in milliseconds.
            site (str): The target site address.
            endpoint (str, optional) The API endpoint
        """
        super().__init__(name, sla_ms, site, endpoint)
        self._json_path = json_path
        self._json_path_expr = jsonpath_ng.parse(json_path)

    def extract_data(self, body):
        try:
            body_data = json.loads(body)
            match = self._json_path_expr.find(body_data)
            if len(match) > 0:
                # Extract just the first value.
                return html.escape(match[0].value)
            else:
                raise LogExtractionException(
                    "({name}) Could not extract log with jsonpath '{json_path}'.".format(
                        name=self._name, json_path=self._json_path))
        except json.JSONDecodeError:
            raise LogExtractionException("({name}) JSON parse error.".format(
                name=self._name))


class RegexReader(APIReader):

    def __init__(self, name, sla_ms, site, endpoint, regex):
        """
        Args:
            sla_ms (int): The SLA timeout in milliseconds.
            site (str): The target site address.
            regex (str): The regex to use for extracting data from response.
        """
        self._regex = regex
        # Expect multiline input for regex matching.
        self._matcher = re.compile(regex, re.M)
        super().__init__(name, sla_ms, site, endpoint)

    def extract_data(self, body):
        match = self._matcher.search(body)
        if match:
            # Escape in any case.
            return html.escape(match.group(1))
        else:
            raise LogExtractionException(
                "({name}) Could not extract log with regex '{regex}'.".format(
                    name=self._name, regex=self._regex))
