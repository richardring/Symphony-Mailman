# Based on https://gist.github.com/leonjza/b5043b5602e9222e6760
import os
import sqlite3

import botlog as log
from email_server.caching.cache import Cache
import exceptions


class UserCache(Cache):
    _create_sql = 'CREATE TABLE IF NOT EXISTS address_cache '
    _create_sql += '(email TEXT PRIMARY KEY, sym_id TEXT, pod_id TEXT, pretty_name TEXT)'

    _create_index = 'CREATE INDEX IF NOT EXISTS key_index ON address_cache (email)'
    _get_sql = 'SELECT email, sym_id, obo_user_id FROM address_cache WHERE email = ? AND obo_user_id = ?'
    _del_sql = 'DELETE FROM address_cache WHERE email = ?'
    _update_sql = 'REPLACE INTO address_cache (email, sym_id, obo_user_id, pod_id, pretty_name) VALUES (?, ?, ?,  ?, ?)'
    _insert_sql = 'INSERT INTO address_cache (email, sym_id, obo_user_id, pod_id, pretty_name) VALUES (?, ?, ?, ?, ?)'
    _clear_all_sql = 'DELETE FROM address_cache'

    conn = None

    def __init__(self, cache_config):
        # I don't know if this is necessary or not
        super().__init__(cache_config)
        self._cache_config = cache_config

    def Get_Connection(self):
        if self.conn:
            return self.conn

        try:
            sqlite_file_path = os.path.abspath(self._cache_config['path'])
            sqlite_filename = self._cache_config['filename']

            db_path = os.path.join(sqlite_file_path, sqlite_filename)

            log.LogConsoleInfoVerbose('Establishing SQLite connection to ' + db_path)
            self.conn = sqlite3.Connection(db_path, timeout=60)
            # Row Factory enables referencing cells by column name
            # https://docs.python.org/3/library/sqlite3.html#accessing-columns-by-name-instead-of-by-index
            self.conn.row_factory = sqlite3.Row

            # Run the initialization SQL. Each of the "create" SQL statements starts with
            # "IF NOT EXISTS" so it should not blow away the database if it's already there.
            log.LogConsoleInfoVerbose('Initializing database...')
            with self.conn:
                self.conn.execute(self._create_sql)
                self.conn.execute(self._create_index)
        except Exception as ex:
            exceptions.LogException(ex)

        return self.conn

    def Get_Id(self, email_address: str, obo_user_id: str):
        user_id = ''
        pretty_name = ''
        with self.Get_Connection() as conn:
            for row in conn.execute(self._get_sql, (email_address, obo_user_id,)):
                # There should only be one row for each email
                user_id = str(row['sym_id'])
                pretty_name = str(row['pretty_name'])
                break

        return user_id, pretty_name

    def Delete_Id(self, email_address):
        with self.conn as conn:
            conn.execute(self._del_sql, (email_address,))

    def Update_Id(self, email_address: str, sym_id: str, obo_user_id: str, pod_id: str, pretty_name: str=''):

        with self.Get_Connection() as conn:
            conn.execute(self._update_sql, (email_address, sym_id, obo_user_id, pod_id, pretty_name))

    def Insert_Id(self, email_address: str, sym_id: str, obo_user_id: str, pod_id: str, pretty_name: str=''):
        with self.Get_Connection() as conn:
            try:
                conn.execute(self._insert_sql, (email_address, sym_id, obo_user_id, pod_id, pretty_name))
            except sqlite3.IntegrityError:
                # attempt to store a duplicate entry
                log.LogSystemWarn('Attempt to insert an existing email into the cache (' + email_address + ')')
                self.Update_Id(email_address, sym_id, obo_user_id, pod_id, pretty_name)
                pass

    def Clear_All(self):
        with self.Get_Connection() as conn:
            conn.execute(self._clear_all_sql)

    def __del__(self):
        if self.conn:
            self.conn.close()