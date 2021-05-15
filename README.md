# API status monitor

Project contains a website availability producer and consumer.
The producer asynchronously requests multiple web pages and publishes status information to Kafka topic.
The consumer reads published messages from the topic and writes the data to PostgreSQL database.

## Requirements

 * Python >3.8
 * Python virtualenv
 * Docker >1.13.0
 * Kafka >2.6 in Cloud setup
 * PostgreSQL >12 in Cloud setup

To install everything needed in pristine Ubuntu 20.04 run the script with `sudo` [bootstrap.sh](bootstrap.sh).
Script enables the `docker` group for the session, but to get the group to globally affect all sessions a log out and log in is needed.

## Quick start

Example has a help script [run-demo.sh](run-demo.sh) to run everything with single command. This creates virtual environment for Python, install dependencies, builds the distribution package, setups Docker containers and launches the containers.

In the `cloud` setup the demo expects to have Kafka SSL certificates in `certs` directory.
The expected files are `ca.pem`, `service.cert` and `service.key`.
The `local` setup does not use SSL.

```bash
$ run-demo.sh [local|cloud]
```

Typical Cloud setup start command template. This command expects that single user with administrative privileges is used to create the database and migrate the tables and to connect the application database:

```bash
$ KAFKAHOST="<KAFKA-HOST>:<KAFKA-PORT>" PGHOST="<POSTGRES-HOST>" PGPORT="<POSTGRES-PORT>" PGUSER="<POSTGRES-USER>" PGPW="<POSTGRES-PASSWORD>" ./run-demo.sh cloud"
```

Stop everything with **'Crtl+C'**.

## Development setup

```bash
$ python3 -m venv apistatus-venv
$ source apistatus-venv/bin/activate
$ pip install -e [.dev]
```

## Building

```bash
$ python3 -m build
```

## Tests

```bash
$ coverage run --source=. -m unittest
$ coverage html --omit=tests/**,venv/**
$ open htmlcov/index.html
```

## Running in Docker Compose

To run the local integration setup. Please configure the environment variables accordingly.

```bash
$ docker-compose up -d
```

### Producer environment variables

 * LOG_LEVEL (default: WARNING)
 * KAFKA_BOOTSTRAP_SERVERS (default: localhost:9092)
 * KAFKA_STATUS_TOPIC (default: statuses)
 * KAFKA_SSL_CA_FILE
 * KAFKA_SSL_CERT_FILE
 * KAFKA_SSL_KEY_FILE
 * READER_CONF_FILE (default: conf/apireader)

```bash
$ <ENVIRONMENT VARIABLES> ./src/producer/producer.py
```

### Consumer environment variables

 * LOG_LEVEL (default: WARNING)
 * KAFKA_BOOTSTRAP_SERVERS (default: localhost:9092)
 * KAFKA_STATUS_TOPIC (default: statuses)
 * KAFKA_SSL_CA_FILE
 * KAFKA_SSL_CERT_FILE
 * KAFKA_SSL_KEY_FILE
 * PGHOST (default: localhost)
 * PGPORT (default: 5432)
 * PGSSLMODE (default: None)
 * PGUSER (default: postgres)
 * PGPW (default: postgres)
 * PGAPPUSER (default: postgres)
 * PGAPPPW (default: postgres)
 * PGDB (default: postgres)
 * APPDB (default: api_statuses)

```bash
$ <ENVIRONMENT VARIABLES> ./src/consumer/consumer.py
```

The administrative and application database user and password are separated. This allows to have correct privileges for migrations and administrative actions and reduced privileges for applications access.

## Adding new API status monitor

The [conf/apireader.yml](conf/apireader.yml) confíguration file contains the three example API readers. Example support two types of readers, json path and regex. To add a new reader use the existing configuration as a template and point a reader to new site and endpoint. Configure the regular expression or jsonpath to return single element from the returned body data of the site and endpoint.
Fields:
 * `sla_ms` is used to decide if the API test was successful in the sense of API response time.
 * `site` is the target site to monitor.
 * `endpoint` is the target path of the site to monitor.
 * `json_path` expects a json path expression for finding the desired value from the returned JSON response body.
 * `regex` expects a Python regular expression for finding the desired value as first matched group.

## TODO

 * Exception handling is broad and uses Exception in multiple places. Focus has been to avoid application crash instead of control
 * Move database migration responsibility to own module and application.
 * Producer and consumer expect that Kafka and PostgreSQL are available immediately. This should be changed to conform with 12 fractured apps and applications to retry connections with backoff.
