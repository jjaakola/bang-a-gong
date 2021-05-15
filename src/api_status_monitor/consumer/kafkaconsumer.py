"""The API status information consumer.
"""

import logging


class APIStatusKafkaConsumer():
    """APIStatusKafkaConsumer is tied to consume single topic given
    as :status_topic.

    All parameters are required to be valid objects.
    """

    def __init__(self, status_topic, kafka_consumer, database_writer):
        assert status_topic is not None
        assert kafka_consumer is not None
        assert database_writer is not None
        self.consumer = kafka_consumer
        self.status_topic = status_topic
        self.consumer.subscribe(self.status_topic)
        self.database_writer = database_writer

    def close(self):
        """Closes the Kafka consumer and the database writer.
        """
        logging.info("Closing consumer.")
        try:
            self.consumer.close()
            self.database_writer.close()
        except Exception:
            logging.warning("Consumer close raised an exception.", exc_info=1)
        logging.info("Consumer closed.")

    def consume(self):
        """Poll messages instead of using the consumer iterator.
        Using poll gives better control to shutdown after reading
        a batch of messages.
        """

        topics = self.consumer.poll(timeout_ms=100)
        for topic, messages in topics.items():
            for message in messages:
                logging.debug("Topic: %s and value %s", topic, message.value)
                try:
                    self.database_writer.persist(message.value)
                except Exception:
                    logging.warning("Database writing failed.", exc_info=1)
        self. consumer.commit()
