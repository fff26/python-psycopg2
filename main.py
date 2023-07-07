import psycopg2

class Client:
    def __init__(self, first_name, last_name, email, phones=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phones = phones or []

    def add_phone(self, phone):
        self.phones.append(phone)

    def remove_phone(self, phone):
        self.phones.remove(phone)

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phones": self.phones
        }

class Database:
    def __init__(self, database_name, user, password):
        self.conn = psycopg2.connect(database=database_name, user=user, password=password)

    def create_clients_table(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                DROP TABLE IF EXISTS clients;
                """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id SERIAL PRIMARY KEY,
                    first_name VARCHAR(40),
                    last_name VARCHAR(40),
                    email VARCHAR(80),
                    phones VARCHAR(30)[]
                )
            """)
            self.conn.commit()

    def add_client(self, client):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO clients (first_name, last_name, email, phones)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (client.first_name, client.last_name, client.email, client.phones))
            client_id = cur.fetchone()
        return client_id

    def get_client_by_id(self, client_id):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM clients
                WHERE id = %s
            """, (client_id,))
            result = cur.fetchone()
        if result is None:
            return None
        return Client(*result[1:])

    def get_clients_by_params(self, first_name=None, last_name=None, email=None, phone=None):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM clients
                WHERE (%s IS NULL OR first_name = %s)
                  AND (%s IS NULL OR last_name = %s)
                  AND (%s IS NULL OR email = %s)
                  AND (%s IS NULL OR %s = ANY(phones))
            """, (first_name, first_name, last_name, last_name, email, email, phone, phone))
            results = cur.fetchall()
        return [Client(*result[1:]) for result in results]

    def update_client(self, client_id, **client_data):
        client = self.get_client_by_id(client_id)
        if client is None:
            return
        for key, value in client_data.items():
            if key == "phones":
                if value is None:
                    client.phones = []
                else:
                    client.phones = value
            else:
                setattr(client, key, value)
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE clients
                SET first_name = %s, last_name = %s, email = %s, phones = %s
                WHERE id = %s;
            """, (client.first_name, client.last_name, client.email, client.phones, client_id))
            self.conn.commit()

    def remove_client(self, client_id):
        with self.conn.cursor() as cur:
            cur.execute("""
                DELETE FROM clients
                WHERE id = %s;
            """, (client_id,))

    def close(self):
        self.conn.close()

# __________________
# Создание экземпляра класса Database
db = Database(database_name="clients_db", user="postgres", password="postgres")

# Создание таблицы clients
db.create_clients_table()

# Добавление клиентов
client1 = Client("Иван", "Ивановский", "ivnanushka@mail.ru", ["+7 211 122-17-12", "+7 122 211-92-11"])
client1_id = db.add_client(client1)

client2 = Client("Петр", "Петров", "petya_petrov@yandex.ru", ["+7 333 222-11-00"])
client2_id = db.add_client(client2)

client3 = Client("Сидр", "Сидорин", "mister-sidr@ne-pey.ego")
client3_id = db.add_client(client3)

# Добавление телефонов
client1.add_phone("+7 981 010-99-44")
db.update_client(client1_id, phones=client1.phones)

client2.add_phone("+7 916 555-77-38")
db.update_client(client2_id, phones=client2.phones)

# Поиск клиентов по различным параметрам
print(db.get_clients_by_params(first_name="Иван"))
# -> [Client(first_name='Иван', last_name='Ивановский', email='ivnanushka@mail.ru', phones=['+7 211 122-17-12', '+7 122 211-92-11'])]

print(db.get_clients_by_params(email="petya_petrov@yandex.ru"))
# -> [Client(first_name='Петр', last_name='Петров', email='petya_petrov@yandex.ru', phones=['+7 333 222-11-00'])]

# Изменение данных клиента
db.update_client(client3_id, last_name="Новофамильский", phones=["+7 978 888-77-55"])

# Удаление клиента
db.remove_client(client2_id)

# Закрытие соединения с базой данных
db.close()