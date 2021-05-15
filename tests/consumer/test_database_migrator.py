import unittest
from unittest.mock import call, patch, Mock
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import api_status_monitor.consumer.database_migrator
from api_status_monitor.consumer.database_migrator \
    import DatabaseMigrator, MigrationException


class TestDatabaseMigrator(unittest.TestCase):

    @patch(
        'api_status_monitor.consumer.database_connection.DatabaseConnection')
    def test_create_database(self, mock_cm):
        mock_conn = Mock()
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = False
        mock_cm.get_connection.return_value = mock_conn

        dm = DatabaseMigrator(mock_cm)
        dm.create_database()

        mock_conn.set_isolation_level.assert_called_once_with(ISOLATION_LEVEL_AUTOCOMMIT)
        mock_conn.cursor.assert_called_once()
        mock_cur.fetchone.assert_called_once()
        mock_cur.execute.assert_has_calls(
            [call(api_status_monitor.consumer.database_migrator.CHECK_DATABASE),
             call(api_status_monitor.consumer.database_migrator.CREATE_DATABASE)]
        )
        mock_cm.close.assert_called_once()

    @patch(
        'api_status_monitor.consumer.database_connection.DatabaseConnection')
    def test_create_database_error(self, mock_cm):
        mock_cm.get_connection.return_value = None

        dm = DatabaseMigrator(mock_cm)
        with self.assertRaises(MigrationException):
            dm.create_database()

    @patch(
        'api_status_monitor.consumer.database_connection.DatabaseConnection')
    def test_migrate_ok_create_database(self, mock_cm):
        mock_conn = Mock()
        mock_cur = Mock()
        mock_conn.cursor.return_value = mock_cur
        mock_cm.get_connection.return_value = mock_conn

        dm = DatabaseMigrator(mock_cm)
        dm.migrate()

        mock_conn.cursor.assert_called_once()
        mock_cur.execute.assert_has_calls(
            [call(api_status_monitor.consumer.database_migrator.CREATE_SITES_TABLE),
             call(api_status_monitor.consumer.database_migrator.CREATE_SITES_INDEX),
             call(api_status_monitor.consumer.database_migrator.CREATE_STATUS_TABLE)]
        )
        # sites, sites index, status and 12 partition tables.
        self.assertEqual(16, mock_cur.execute.call_count)
        mock_conn.commit.assert_called_once()
        mock_cm.close.assert_called_once()

    @patch(
        'api_status_monitor.consumer.database_connection.DatabaseConnection')
    def test_migrate_error(self, mock_cm):
        mock_cm.get_connection.return_value = None

        dm = DatabaseMigrator(mock_cm)
        with self.assertRaises(MigrationException):
            dm.migrate()
