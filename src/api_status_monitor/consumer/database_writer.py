"""The database writer for API status information.
"""

import logging
from datetime import datetime
from psycopg2 import sql


INSERT_STATUS = sql.SQL("""
WITH site_uuid AS (INSERT INTO sites (site) VALUES ({site})
  ON CONFLICT ON CONSTRAINT sites_site_key
  DO UPDATE SET site=EXCLUDED.site RETURNING id)
INSERT INTO api_status
  (site_id, endpoint, status_code, response_time_ms, sla_ms, success, ts, log, error)
  SELECT id, {endpoint}, {status_code}, {response_time}, {sla_ms}, {success}, {ts}, {log}, {error}
  FROM site_uuid
""")
"""
Insert the site to sites table and return the existing primary
key on conflict. The DO UPDATE with the exclusion is needed for
the RETURNING to return the value. DO NOTHING really means do
nothing on conflict.

The insertion to api_status selects the site primary key from
the result of `WITH site_uuid`.
"""


class DatabaseWriter():

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager

    def close(self):
        self.connection_manager.close()

    def persist(self, status):
        conn = self.connection_manager.get_connection()
        if conn:
            cur = conn.cursor()
            insert_status = INSERT_STATUS.format(
                site=sql.Literal(status.site),
                endpoint=sql.Literal(status.endpoint),
                status_code=sql.Literal(status.status_code),
                response_time=sql.Literal(status.response_time_ms),
                sla_ms=sql.Literal(status.sla_ms),
                success=sql.Literal(status.success()),
                ts=sql.Literal(datetime.fromtimestamp(status.timestamp)),
                log=sql.Literal(status.log),
                error=sql.Literal(status.error)
                )
            try:
                cur.execute(insert_status)
                conn.commit()
            except Exception:
                logging.warning("Could not insert to api statuses", exc_info=1)
                conn.rollback()
        else:
            logging.warning("Could not persist API status information.")
