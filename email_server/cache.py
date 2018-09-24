# Based on https://gist.github.com/leonjza/b5043b5602e9222e6760
import sqlite3

import botlog as log
import config
import exceptions


class EmailCache:
    _create_sql = 'CREATE TABLE IF NOT EXISTS address_cache (email TEXT PRIMARY KEY, sym_id TEXT)'
    _create_index = 'CREATE INDEX IF NOT EXISTS key_index ON address_cache (email)'
    _get_sql = 'SELECT email, sym_id FROM address_cache WHERE email = ?'
    _del_sql = 'DELETE FROM address_cache WHERE email = ?'
    _update_sql = 'REPLACE INTO address_cache (email, sym_id) VALUES (?, ?)'
    _insert_sql = 'INSERT INTO address_cache (email, sym_id) VALUES (?, ?)'
    _clear_all_sql = 'DELETE FROM address_cache'

    conn = None

    def __init__(self):
        pass

    def Get_Conn(self):
        if self.conn:
            return self.conn

        try:
            db_path = config.CachePath

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

    def Get_Id(self, email_address):
        retval = None
        with self.Get_Conn() as conn:
            for row in conn.execute(self._get_sql, (email_address,)):
                # There should only be one row for each email
                retval = str(row['sym_id'])
                break

        return retval

    def Delete_Id(self, email_address):
        with self.conn as conn:
            conn.execute(self._del_sql, (email_address,))

    def Update_Id(self, email_address, sym_id):

        with self.Get_Conn() as conn:
            conn.execute(self._update_sql, (email_address, sym_id))

    def Insert_Id(self, email_address, sym_id):
        with self.Get_Conn() as conn:
            try:
                conn.execute(self._insert_sql, (email_address, sym_id))
            except sqlite3.IntegrityError:
                # attempt to store a duplicate entry
                log.LogSystemWarn('Attempt to insert an existing email into the cache (' + email_address + ')')
                self.Update_Id(email_address, sym_id)
                pass

    def Clear_All(self):
        with self.Get_Conn() as conn:
            conn.execute(self._clear_all_sql)

    def __del__(self):
        if self.conn:
            self.conn.close()