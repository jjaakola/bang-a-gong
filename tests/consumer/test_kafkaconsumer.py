import unittest
from unittest.mock import patch
from collections import namedtuple
from api_status_monitor.consumer.kafkaconsumer import APIStatusKafkaConsumer


class TestKafkaConsumer(unittest.TestCase):

    @patch('kafka.KafkaConsumer')
    @patch('api_status_monitor.consumer.database_writer.DatabaseWriter')
    def test_init_consumer(self, mock_kafka_consumer, mock_db_writer):
        consumer = APIStatusKafkaConsumer("statuses",
                                          mock_kafka_consumer, mock_db_writer)
        consumer.consume()
        mock_kafka_consumer.subscribe.assert_called_once_with("statuses")

    @patch('kafka.KafkaConsumer')
    @patch('api_status_monitor.consumer.database_writer.DatabaseWriter')
    def test_consume_no_data(self, mock_kafka_consumer, mock_db_writer):
        consumer = APIStatusKafkaConsumer("statuses",
                                          mock_kafka_consumer, mock_db_writer)
        consumer.consume()
        mock_kafka_consumer.poll.assert_called_once_with(timeout_ms=100)
        mock_db_writer.persist.assert_not_called()

    @patch('kafka.KafkaConsumer')
    @patch('api_status_monitor.consumer.database_writer.DatabaseWriter')
    def test_consume_topic_no_messages(self,
                                       mock_kafka_consumer, mock_db_writer):
        consumer = APIStatusKafkaConsumer("statuses",
                                          mock_kafka_consumer, mock_db_writer)
        mock_kafka_consumer.poll.return_value = {
            "statuses": []
            }
        consumer.consume()
        mock_kafka_consumer.poll.assert_called_once_with(timeout_ms=100)
        mock_db_writer.persist.assert_not_called()

    @patch('kafka.KafkaConsumer')
    @patch('api_status_monitor.consumer.database_writer.DatabaseWriter')
    def test_consume_topic_two_messages(
            self, mock_kafka_consumer, mock_db_writer):
        MessageData = namedtuple("MessageData", ["value"])
        consumer = APIStatusKafkaConsumer("statuses",
                                          mock_kafka_consumer, mock_db_writer)
        mock_kafka_consumer.poll.return_value = {
            "statuses": [MessageData("msg1"), MessageData("msg2")]
            }
        consumer.consume()
        mock_kafka_consumer.poll.assert_called_once_with(timeout_ms=100)
        mock_db_writer.persist.assert_has_calls(mock_db_writer.persist("msg1"),
                                                mock_db_writer.persist("msg2"))

    @patch('kafka.KafkaConsumer')
    @patch('api_status_monitor.consumer.database_writer.DatabaseWriter')
    def test_consume_database_persist_raises_exception(
            self, mock_kafka_consumer, mock_db_writer):
        MessageData = namedtuple("MessageData", ["value"])
        consumer = APIStatusKafkaConsumer("statuses",
                                          mock_kafka_consumer, mock_db_writer)
        mock_kafka_consumer.poll.return_value = {
            "statuses": [MessageData("raises exception")]
            }
        mock_db_writer.persist.side_effect = Exception("error")
        consumer.consume()
        mock_kafka_consumer.poll.assert_called_once_with(timeout_ms=100)
        mock_db_writer.persist.assert_called_once_with("raises exception")

    @patch('kafka.KafkaConsumer')
    @patch('api_status_monitor.consumer.database_writer.DatabaseWriter')
    def test_consumer_close(self, mock_kafka_consumer, mock_db_writer):
        consumer = APIStatusKafkaConsumer("statuses",
                                          mock_kafka_consumer, mock_db_writer)
        consumer.close()
        mock_kafka_consumer.close.assert_called_once()
        mock_db_writer.close.assert_called_once()

    @patch('kafka.KafkaConsumer')
    @patch('api_status_monitor.consumer.database_writer.DatabaseWriter')
    def test_consumer_close_raises_exception(self, mock_kafka_consumer,
                                             mock_db_writer):
        consumer = APIStatusKafkaConsumer("statuses",
                                          mock_kafka_consumer, mock_db_writer)
        mock_db_writer.close.side_effect = Exception("error")
        consumer.close()
        mock_kafka_consumer.close.assert_called_once()
        mock_db_writer.close.assert_called_once()
