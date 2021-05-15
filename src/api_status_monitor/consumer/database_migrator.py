"""Database migrator.

Creates 'api_statuses' database if it does not exist.
Enables the 'pgcrypto' extension if not enabled for gen_random_uuid() function.
Create the 'sites' table and 'api_statuses' tables if those does not exist.
"""

import logging
from datetime import datetime, timedelta
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


CHECK_DATABASE = """
SELECT 1 FROM pg_database WHERE pg_database.datname = 'api_statuses'
"""
CREATE_DATABASE = "CREATE DATABASE api_statuses"
ENABLE_PGCRYPTO = "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\""
CREATE_STATUS_TABLE = """
CREATE TABLE IF NOT EXISTS api_status (
  site_id           uuid NOT NULL,
  endpoint          varchar(255) NOT NULL,
  status_code       smallint NOT NULL,
  response_time_ms  smallint NOT NULL,
  sla_ms            smallint NOT NULL,
  success           boolean NOT NULL,
  ts                timestamp without time zone NOT NULL,
  log               varchar(255),
  error             varchar(255),
  CONSTRAINT fk_site FOREIGN KEY (site_id) REFERENCES sites(id)
) PARTITION BY RANGE (EXTRACT(YEAR FROM ts), EXTRACT(MONTH FROM ts))
"""
"""
The sla_ms could be in the sites table. The difference is if sla_ms
would be changed it would change also the history. The change would
be global when looking from the rows in the api_status.
This is the reason it is in api_status and in this exercise redundant.

Partitioning of data is for each month.
If API/webpage status is monitored twice a minute, the row count
for each month is ~87600 for each monitored API/webpage.
The old partitions can be detached and archived.
"""

CREATE_API_STATUS_PARTITIONS_TMPL = """
CREATE TABLE IF NOT EXISTS api_status_{year}_{month}
  PARTITION OF api_status (ts default '{year}-{month}-01')
  FOR VALUES FROM ({year}, {month}) TO ({year_n}, {month_n})
"""

CREATE_SITES_TABLE = """
CREATE TABLE IF NOT EXISTS sites (
  id    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  site  varchar(255) UNIQUE
)
"""
"""
The primary key is random uuid to counter the enumeration attack.
"""

CREATE_SITES_INDEX = """
CREATE INDEX IF NOT EXISTS sites_index ON sites (site)
"""


class DatabaseMigrator():
    """DatabaseMigrator requires the connection manager to be
    created with administrative privileges.
    """
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager

    def create_database(self):
        conn = self.connection_manager.get_connection()
        if conn:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = self.connection_manager.get_connection().cursor()
            cur.execute(CHECK_DATABASE)
            res = cur.fetchone()
            if not res:
                logging.info("Database api_statuses does not exist. Creating.")
                cur.execute(CREATE_DATABASE)
            conn.commit()
            self.connection_manager.close()
        else:
            raise MigrationException("Could not create the database.")

    def migrate(self):
        conn = self.connection_manager.get_connection()
        if conn:
            cur = conn.cursor()
            cur.execute(ENABLE_PGCRYPTO)
            cur.execute(CREATE_SITES_TABLE)
            cur.execute(CREATE_SITES_INDEX)
            cur.execute(CREATE_STATUS_TABLE)

            # Create api status data partitions twelve months ahead.
            # Get the first day of the month.
            current_month = datetime.today().date().replace(day=1)
            for i in range(12):
                year = current_month.strftime("%Y")
                month = current_month.strftime("%m")
                # Add 32 days to move datetime enough in future
                # to roll the month. The current month always has
                # the first day set so it is safe to add 32 days.
                # The boundary test would be on January due to
                # February having 28/29 days and others 31 or 30
                # days. So 32 days will always roll to next month.
                next_month = (current_month + timedelta(days=32)) \
                    .replace(day=1)
                year_of_next_month = next_month.strftime("%Y")
                month_of_next_month = next_month.strftime("%m")

                create_partition = CREATE_API_STATUS_PARTITIONS_TMPL.format(
                    year=year, month=month, year_n=year_of_next_month,
                    month_n=month_of_next_month)
                cur.execute(create_partition)

                current_month = next_month

            conn.commit()
            self.connection_manager.close()
        else:
            raise MigrationException("Could not migrate the database.")


class MigrationException(Exception):
    pass
