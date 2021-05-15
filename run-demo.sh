#!/usr/bin/env bash

set -eo pipefail

TARGET_ENVIRONMENT="${1:-local}"
if [[ $TARGET_ENVIRONMENT == "local" ]]; then
    echo "Running to local test environment."
elif [[ $1 == "cloud" ]]; then
    if [ -z "$(ls -A ./certs)" ]; then
	echo "Expected SSL certificate directory './certs' to contain files."
	echo "Please get the Kafka certificates and place them in './certs'."
	echo "Expected files are './certs/ca.pem', './certs/service.cert' and './certs/service.key'."
	exit 1
    fi

    set -u

    echo "Running to cloud."
    echo "Kafka address:     $KAFKAHOST"
    echo "PostgreSQL address $PGHOST:$PGPORT"
    echo "PostgreSQL user:   $PGUSER"
    # Refer the environment variable for 'set -u'
    PGPW="$PGPW"
else
    echo "Unknown target environment."
    echo "Usage: $0 [local|cloud]"
    exit 1
fi

echo "Create virtual environment 'venv'."
python3 -m venv venv
. ./venv/bin/activate

echo "Install development requirements"
pip install -e .[dev]

echo "Running tests."
coverage run --source=. -m unittest

echo "Building dist package."
python3 -m build

echo "Building producer and consumer Docker containers."
docker build --build-arg command=produce -t producer:latest  .
docker build --build-arg command=consume -t consumer:latest  .

echo "Running in Docker Compose."
docker-compose -f docker-compose.yml -f "docker-compose.$TARGET_ENVIRONMENT.yml" up
