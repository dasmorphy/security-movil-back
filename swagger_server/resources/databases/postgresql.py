import psycopg2
from psycopg2.extras import RealDictCursor
from swagger_server.config.access import access


class PostgreSQLConnection:
    def __init__(self):
        self.config = access()['DB']['POSTGRESQL']['FLASK_APP']
        self.connection = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                host=self.config['HOST'],
                database=self.config['DB'],
                user=self.config['USER'],
                password=self.config['PASSWORD'],
                port=self.config['PORT']
            )
            return self.connection
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {e}")
            return None

    def execute_query(self, query, params=None):
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                
                if query.strip().upper().startswith(('SELECT', 'RETURNING')):
                    return cursor.fetchall()
                else:
                    self.connection.commit()
                    return cursor.rowcount
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            print(f"Error executing query: {e}")
            return None

    def close(self):
        if self.connection:
            self.connection.close()
