import asyncio
import time
import unittest
from aioresponses import CallbackResult, aioresponses
from api_status_monitor.producer.apireaders import create_reader


WORLD_CLOCK_RESPONSE_STRING = '{"$id":"1","currentDateTime":"2021-05-12T20:23Z","utcOffset":"00:00:00","isDayLightSavingsTime":false,"dayOfTheWeek":"Wednesday","timeZoneName":"UTC","currentFileTime":132653246052918702,"ordinalDate":"2021-132","serviceResponse":null}'


class TestWorldClockReader(unittest.IsolatedAsyncioTestCase):

    @aioresponses()
    async def test_read(self, mocked):
        loop = asyncio.get_event_loop()
        mocked.get("http://worldclockapi.com/api/json/utc/now",
                   status=200, body=WORLD_CLOCK_RESPONSE_STRING)

        reader = create_reader(name="worldclock", type="json", sla_ms=100,
                               site="http://worldclockapi.com",
                               endpoint="/api/json/utc/now",
                               json_path="$.currentDateTime")
        s = await reader.read()

        self.assertEqual(200, s.status_code)
        self.assertTrue(s.success())
        self.assertEqual("2021-05-12T20:23Z", s.log)
        self.assertEqual("", s.error)
        self.assertTrue(s.in_sla())

    @aioresponses()
    async def test_over_sla(self, mocked):
        def request_callback(url, **kwargs):
            # burn some time for sla to fail
            time.sleep(0.5)
            headers = {'content-type': 'application/json'}
            return CallbackResult(status=200, body=WORLD_CLOCK_RESPONSE_STRING,
                                  headers=headers)

        loop = asyncio.get_event_loop()
        mocked.get("http://worldclockapi.com/api/json/utc/now",
                   callback=request_callback)

        reader = create_reader(name="worldclock", type="json", sla_ms=100,
                               site="http://worldclockapi.com",
                               endpoint="/api/json/utc/now",
                               json_path="$.currentDateTime")
        s = await reader.read()

        self.assertEqual(200, s.status_code)
        self.assertTrue(s.success())
        self.assertEqual("2021-05-12T20:23Z", s.log)
        self.assertEqual("", s.error)
        self.assertFalse(s.in_sla())

    @aioresponses()
    async def test_read_error_response(self, mocked):
        loop = asyncio.get_event_loop()
        mocked.get("http://worldclockapi.com/api/json/utc/now",
                   status=500, body="")

        reader = create_reader(name="worldclock", type="json", sla_ms=100,
                               site="http://worldclockapi.com",
                               endpoint="/api/json/utc/now",
                               json_path="$.currentDateTime")
        s = await reader.read()

        self.assertEqual(500, s.status_code)
        self.assertFalse(s.success())
        self.assertEqual("", s.log)
        self.assertEqual("(worldclock) JSON parse error.", s.error)
        self.assertTrue(s.in_sla())

    @aioresponses()
    async def test_read_invalid_json_response(self, mocked):
        loop = asyncio.get_event_loop()
        mocked.get("http://worldclockapi.com/api/json/utc/now",
                   status=200, body="{}")

        reader = create_reader(name="worldclock", type="json", sla_ms=100,
                               site="http://worldclockapi.com",
                               endpoint="/api/json/utc/now",
                               json_path="$.currentDateTime")
        s = await reader.read()

        self.assertEqual(200, s.status_code)
        self.assertFalse(s.success())
        self.assertEqual("", s.log)
        self.assertEqual(
            "(worldclock) Could not extract log with jsonpath '$.currentDateTime'.",
            s.error)
        self.assertTrue(s.in_sla())

    @aioresponses()
    async def test_read_error(self, mocked):
        loop = asyncio.get_event_loop()
        mocked.get("http://worldclockapi.com/api/json/utc/now",
                   exception=Exception("error"))

        reader = create_reader(name="worldclock", type="json", sla_ms=100,
                               site="http://worldclockapi.com",
                               endpoint="/api/json/utc/now",
                               json_path="$.currentDateTime")
        s = await reader.read()

        self.assertEqual(0, s.status_code)
        self.assertFalse(s.success())
        self.assertEqual("", s.log)
        self.assertEqual("error", s.error)
        self.assertTrue(s.in_sla())

    @aioresponses()
    async def test_read_timeout_error(self, mocked):
        loop = asyncio.get_event_loop()
        mocked.get("http://worldclockapi.com/api/json/utc/now",
                   exception=asyncio.exceptions.TimeoutError)

        reader = create_reader(name="worldclock", type="json", sla_ms=100,
                               site="http://worldclockapi.com",
                               endpoint="/api/json/utc/now",
                               json_path="$.currentDateTime")
        s = await reader.read()

        self.assertEqual(0, s.status_code)
        self.assertFalse(s.success())
        self.assertEqual("", s.log)
        self.assertEqual("TIMEOUT", s.error)
        self.assertTrue(s.in_sla())


JPX_RESPONSE_STRING = """
<html>
<title>Test title</title>
<body>
</body>
</html>
"""


class JapanStockExchangeReaderTest(unittest.IsolatedAsyncioTestCase):

    @aioresponses()
    async def test_read(self, mocked):
        loop = asyncio.get_event_loop()
        mocked.get("https://www.jpx.co.jp",
                   status=200, body=JPX_RESPONSE_STRING)

        reader = create_reader(name="jpx", type="regex", sla_ms=100,
                               site="https://www.jpx.co.jp",
                               endpoint="/",
                               regex="<title>([\w\s]*)</title>")
        s = await reader.read()

        self.assertEqual(200, s.status_code)
        self.assertTrue(s.success())
        self.assertEqual("Test title", s.log)
        self.assertEqual("", s.error)
        self.assertTrue(s.in_sla())

    @aioresponses()
    async def test_read_no_title(self, mocked):
        loop = asyncio.get_event_loop()
        mocked.get("https://www.jpx.co.jp",
                   status=200, body="No title in the response")

        reader = create_reader(name="jpx", type="regex", sla_ms=100,
                               site="https://www.jpx.co.jp",
                               endpoint="/",
                               regex="<title>([\w\s]*)</title>")
        s = await reader.read()

        self.assertEqual(200, s.status_code)
        self.assertFalse(s.success())
        self.assertEqual("", s.log)
        self.assertEqual("(jpx) Could not extract log with regex '<title>([\\w\\s]*)</title>'.",
                         s.error)
        self.assertTrue(s.in_sla())


AIVEN_RESPONSE_STRING = """
Freedom to build awesome applications
Aiven manages your open source data infrastructure in the cloud - so you don't have to.
"""


class AivenRootReaderTest(unittest.IsolatedAsyncioTestCase):

    @aioresponses()
    async def test_read(self, mocked):
        loop = asyncio.get_event_loop()
        mocked.get("https://aiven.io",
                   status=200, body=AIVEN_RESPONSE_STRING)

        reader = create_reader(name="aiven", type="regex", sla_ms=100,
                               site="https://aiven.io",
                               endpoint="/",
                               regex="(Freedom to build awesome applications)")
        s = await reader.read()

        self.assertEqual(200, s.status_code)
        self.assertTrue(s.success())
        self.assertEqual("Freedom to build awesome applications", s.log)
        self.assertEqual("", s.error)
        self.assertTrue(s.in_sla())

    @aioresponses()
    async def test_read_no_awesomeness(self, mocked):
        loop = asyncio.get_event_loop()
        mocked.get("https://aiven.io",
                   status=200, body="No awesomeness in the response")

        reader = create_reader(name="aiven", type="regex", sla_ms=100,
                               site="https://aiven.io",
                               endpoint="/",
                               regex="(Freedom to build awesome applications)")
        s = await reader.read()

        self.assertEqual(200, s.status_code)
        self.assertFalse(s.success())
        self.assertEqual("", s.log)
        self.assertEqual("(aiven) Could not extract log with regex '(Freedom to build awesome applications)'.",
                         s.error)
        self.assertTrue(s.in_sla())
