import asyncio
import unittest
from unittest.mock import patch, Mock
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError
from api_status_monitor.producer import Producer


class TestProducer(unittest.IsolatedAsyncioTestCase):

    @patch('api_status_monitor.producer.Producer._get_admin_client')
    def test_create_topic(self, mock_admin_client_getter):
        admin_client_mock = Mock()
        mock_admin_client_getter.return_value = admin_client_mock
        producer = Producer({}, "bs_servers", "topic", {'kw': 'args'})
        producer.create_topic()

        topic = NewTopic(name="topic", num_partitions=1, replication_factor=1)
        admin_client_mock.create_topics.assert_called_once()
        admin_client_mock.close.assert_called_once()

    @patch('api_status_monitor.producer.Producer._get_admin_client')
    def test_create_topic_raises_exception(self, mock_admin_client_getter):
        admin_client_mock = Mock()
        mock_admin_client_getter.return_value = admin_client_mock
        admin_client_mock.create_topics.side_effect = \
            TopicAlreadyExistsError("error")
        producer = Producer({}, "bs_servers", "topic", {'kw': 'args'})
        producer.create_topic()

        topic = NewTopic(name="topic", num_partitions=1, replication_factor=1)
        admin_client_mock.create_topics.assert_called_once()
        admin_client_mock.close.assert_called_once()


class TestProducerAsync(unittest.IsolatedAsyncioTestCase):

    @patch('api_status_monitor.producer.Producer._get_kafka_producer')
    @patch('api_status_monitor.producer.Producer.running')
    async def test_read_task(self, mock_running, mock_get_kafka_producer):
        # just one round.
        mock_running.side_effect = [True, False]
        mock_kafka_producer = Mock()
        mock_get_kafka_producer.return_value = mock_kafka_producer
        mock_reader = Mock()
        mock_reader.url.return_value = "url"
        result_future = asyncio.Future()
        result_future.set_result("ok")
        mock_reader.read.return_value = result_future
        loop = asyncio.get_event_loop()
        producer = Producer({}, "bs_servers", "topic", {'kw': 'args'})

        s = await producer.reader_task(mock_reader, 1)
        mock_reader.url.assert_called_once()
        mock_reader.read.assert_called_once()
        mock_get_kafka_producer.assert_called_once()
        mock_kafka_producer.send.assert_called_once()
        mock_kafka_producer.send.assert_called_once_with("topic", "ok")

    @patch('api_status_monitor.producer.Producer._get_kafka_producer')
    @patch('api_status_monitor.producer.Producer.running')
    async def test_read_task_publish_raises_exception(
            self, mock_running, mock_get_kafka_producer):
        # just one round.
        mock_running.side_effect = [True, False]
        mock_kafka_producer = Mock()
        mock_get_kafka_producer.return_value = mock_kafka_producer
        mock_reader = Mock()
        mock_reader.url.return_value = "url"
        result_future = asyncio.Future()
        result_future.set_result("ok")
        mock_reader.read.return_value = result_future
        mock_kafka_producer.send.side_effect = Exception("error")
        loop = asyncio.get_event_loop()
        producer = Producer({}, "bs_servers", "topic", {'kw': 'args'})

        s = await producer.reader_task(mock_reader, 1)
        mock_reader.url.assert_called_once()
        mock_reader.read.assert_called_once()
        mock_get_kafka_producer.assert_called_once()
        mock_kafka_producer.send.assert_called_once_with("topic", "ok")
