"""The database connection manager.
"""

import logging
import psycopg2


class DatabaseConnection():
    """Database connection manager.
    """

    def __init__(self, host, port, user, dbname, password, sslmode):
        self._conn = None
        self._host = host
        self._port = port
        self._user = user
        self._dbname = dbname
        self._password = password
        self._sslmode = "require" if sslmode else None

    def get_connection(self):
        if not self._conn or self._conn.closed:
            try:
                self._conn = psycopg2.connect(dbname=self._dbname,
                                              user=self._user,
                                              host=self._host,
                                              port=self._port,
                                              password=self._password,
                                              sslmode=self._sslmode)
            except Exception:
                logging.error("Unable to connect to PostgreSQL database.", exc_info=1)
                self._conn = None
        return self._conn

    def close(self):
        try:
            if self._conn:
                self._conn.close()
        except Exception:
            logging.warning("Database connection close failed.")
