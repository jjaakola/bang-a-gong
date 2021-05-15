import logging
import asyncio
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from api_status_monitor.producer.apireaders import create_reader


class Producer():

    def __init__(self, reader_configuration, bootstrap_servers, status_topic,
                 kafka_ssl={}):
        """Create the procuducer

        Args:
          reader_configuration (dict): reader configuration dictionary
          bootstrap_servers (str): Kafka bootstrap servers addresses.
          status_topic: The topic to publish the status information.
          kafka_ssl (dict): Kafka SSL connection configuration.
        """
        self.reader_configuration = reader_configuration
        self.bootstrap_servers = bootstrap_servers
        self.status_topic = status_topic
        self._kafka_ssl = kafka_ssl or {}
        if self._kafka_ssl:
            self._kafka_ssl["security_protocol"] = "SSL"
        self._running = False
        self._producer = None

    def _get_admin_client(self):
        return KafkaAdminClient(bootstrap_servers=self.bootstrap_servers,
                                client_id='apistatus_admin', **self._kafka_ssl)

    def create_topic(self):
        admin_client = self._get_admin_client()

        topic_list = []
        topic_list.append(NewTopic(name=self.status_topic, num_partitions=1,
                                   replication_factor=1))
        try:
            admin_client.create_topics(new_topics=topic_list,
                                       validate_only=False)
        except TopicAlreadyExistsError:
            pass
        admin_client.close()

    def _get_kafka_producer(self):
        """Constructs a simple KafkaProducer.
        """
        if self._producer:
            return self._producer
        else:
            try:
                self._producer = \
                    KafkaProducer(bootstrap_servers=self.bootstrap_servers,
                                  client_id="apistatus_producer",
                                  acks="all",
                                  value_serializer=lambda x: x.to_json(),
                                  **self._kafka_ssl)
                return self._producer
            except Exception as e:
                logging.error(
                    "Kafka producer construction raised an exception.",
                    exc_info=1)
                raise e

    def sig_handler(self, signum, frame):
        """Handle signals from OS.
        See main function which signals are routed to this function.

        The event loop is stopped in this signal handler.
        """
        logging.debug("Signal handler called with signal %s.", signum)
        asyncio.get_event_loop().stop()

    def running(self):
        return self._running

    async def reader_task(self, reader, interval):
        while self.running():
            logging.info("Fetching '%s'", reader.url())
            status = await reader.read()
            try:
                self._get_kafka_producer().send(self.status_topic, status)
            except Exception:
                logging.warning("Message publish raised an exception.",
                                exc_info=True)
            await asyncio.sleep(interval)

    def produce(self, api_read_interval_secs):
        """Create the event loop and construct all exported readers
        from the apireaders module.

        And lastly run the loop forever. Signal handler is attached to
        sig_handler and stops the event loop.
        """
        self._running = True
        loop = asyncio.get_event_loop()

        for reader_conf in self.reader_configuration.get('readers', []):
            loop.create_task(
                self.reader_task(create_reader(**reader_conf),
                                 api_read_interval_secs))
        loop.run_forever()
        self._producer.close()
