import logging
from kafka import KafkaConsumer
from api_status_monitor.consumer.kafkaconsumer import APIStatusKafkaConsumer
from api_status_monitor.consumer.database_writer import DatabaseWriter
from api_status_monitor.consumer.database_connection import DatabaseConnection
from api_status_monitor.consumer.database_migrator import DatabaseMigrator
from api_status_monitor.common.apistatus import APIStatusInformation


class Consumer():

    def __init__(self, bootstrap_servers, status_topic, kafka_ssl={}):
        self.bootstrap_servers = bootstrap_servers
        self.status_topic = status_topic
        self._kafka_ssl = kafka_ssl or {}
        if self._kafka_ssl:
            self._kafka_ssl["security_protocol"] = "SSL"
        self.database_writer = None
        self.running = False

    def __create_kafka_consumer(self, bootstrap_servers):
        """Constructs a simple KafkaConsumer.
        """
        return KafkaConsumer(bootstrap_servers=bootstrap_servers,
                             value_deserializer=lambda x: APIStatusInformation.from_json(x),
                             client_id="apistatus_consumer",
                             group_id="apistatus_consumer_group",
                             **self._kafka_ssl)

    def sig_handler(self, signum, frame):
        """Handle signals from OS.
        See main function which signals are routed to this function.

        The loop for calling consumer poll is stopped in this signal handler by
        setting the field 'running' to False.
        """
        logging.debug("Signal handler called with signal %s.", signum)
        self.running = False

    def migrate(self, pghost, pgport, pguser, pgpw, pgdb, appdb, sslmode):
        """Run database migration script.
        """
        connection_manager = DatabaseConnection(pghost, pgport, pguser, pgdb,
                                                pgpw, sslmode)
        DatabaseMigrator(connection_manager).create_database()
        appdb_connection_manager = DatabaseConnection(pghost, pgport, pguser,
                                                      appdb, pgpw, sslmode)
        DatabaseMigrator(appdb_connection_manager).migrate()

    def connect_db(self, pghost, pgport, pguser, apppw, appdb, sslmode):
        """Create the database writer.
        """
        connection_manager = DatabaseConnection(pghost, pgport, pguser, appdb,
                                                apppw, sslmode)
        self.database_writer = DatabaseWriter(connection_manager)

    def run(self):
        """Initialize and start the consumer consuming loop.
        """
        self.running = True
        assert self.database_writer is not None
        consumer = APIStatusKafkaConsumer(
            self.status_topic,
            self.__create_kafka_consumer(self.bootstrap_servers),
            self.database_writer)

        while self.running:
            consumer.consume()

        consumer.close()
        self.database_writer.close()
        logging.info("Exiting")
