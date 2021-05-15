import unittest
from unittest.mock import patch, Mock
from api_status_monitor.consumer.database_connection import DatabaseConnection


class TestDatabaseWriter(unittest.TestCase):

    @patch('psycopg2.connect')
    def test_get_connection_twice_ok_and_close(self, psql):
        mock_conn = Mock()
        mock_conn.closed = False
        psql.return_value = mock_conn

        dc = DatabaseConnection("host", 1212, "user", "dbname", "pw", "require")
        dc.get_connection()
        dc.get_connection()
        dc.close()

        psql.assert_called_once_with(dbname="dbname", user="user",
                                     host="host", port=1212,
                                     password="pw", sslmode="require")
        mock_conn.close.assert_called_once()

    @patch('psycopg2.connect')
    def test_get_connection_error_and_close(self, psql):
        mock_conn = Mock()
        psql.return_value = mock_conn
        dc = DatabaseConnection("host", 1212, "user", "dbname", "pw", "require")
        psql.side_effect = Exception("error")

        dc.get_connection()
        dc.close()

        psql.assert_called_once_with(dbname="dbname", user="user",
                                     host="host", port=1212,
                                     password="pw", sslmode="require")
        mock_conn.close.assert_not_called()

    def test_close(self):
        dc = DatabaseConnection("host", 1212, "user", "dbname", "pw", "require")
        dc.close()

    @patch('psycopg2.connect')
    def test_close_error(self, psql):
        mock_conn = Mock()
        mock_conn.close.side_effect = Exception("error")
        psql.return_value = mock_conn
        dc = DatabaseConnection("host", 1212, "user", "dbname", "pw", "require")
        dc.get_connection()
        dc.close()
