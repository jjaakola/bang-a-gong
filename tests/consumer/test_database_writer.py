import unittest
from unittest.mock import patch, Mock
from api_status_monitor.common.apistatus import APIStatusInformation
from api_status_monitor.consumer.database_writer import DatabaseWriter


class TestDatabaseWriter(unittest.TestCase):

    @patch(
        'api_status_monitor.consumer.database_connection.DatabaseConnection')
    def test_persist_ok(self, mock_cm):
        status = APIStatusInformation("site", "endpoint",
                                      200, "data", "", 1500, 2000)
        db_writer = DatabaseWriter(mock_cm)
        mock_conn = Mock()
        mock_cm.get_connection.return_value = mock_conn
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur

        db_writer.persist(status)
        mock_cm.get_connection.assert_called_once()
        mock_conn.cursor.assert_called_once()
        mock_cur.execute.assert_called_once()

    @patch(
        'api_status_monitor.consumer.database_connection.DatabaseConnection')
    def test_persist_no_connection(self, mock_cm):
        status = APIStatusInformation("site", "endpoint",
                                      200, "data", "", 1500, 2000)
        db_writer = DatabaseWriter(mock_cm)
        mock_cm.get_connection.return_value = None
        db_writer.persist(status)
        mock_cm.get_connection.assert_called_once()

    @patch(
        'api_status_monitor.consumer.database_connection.DatabaseConnection')
    def test_persist_execute_raises_exception(self, mock_cm):
        status = APIStatusInformation("site", "endpoint",
                                      200, "data", "", 1500, 2000)
        db_writer = DatabaseWriter(mock_cm)
        mock_conn = Mock()
        mock_cm.get_connection.return_value = mock_conn
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.execute.side_effect = Exception("error")

        db_writer.persist(status)
        mock_cm.get_connection.assert_called_once()
        mock_conn.rollback.assert_called_once()
