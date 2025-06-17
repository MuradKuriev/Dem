import sqlite3


def create_database():
    conn = sqlite3.connect('obraz_plus.db')
    cursor = conn.cursor()

    # Таблица типов материалов
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS MaterialTypes
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       loss_percentage
                       REAL
                       NOT
                       NULL
                   )
                   ''')

    # Таблица материалов
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS Materials
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       type_id
                       INTEGER,
                       unit_price
                       REAL
                       NOT
                       NULL
                       CHECK
                   (
                       unit_price
                       >=
                       0
                   ),
                       stock_quantity REAL NOT NULL,
                       min_quantity REAL NOT NULL CHECK
                   (
                       min_quantity
                       >=
                       0
                   ),
                       package_quantity REAL NOT NULL,
                       unit_of_measure TEXT NOT NULL,
                       FOREIGN KEY
                   (
                       type_id
                   ) REFERENCES MaterialTypes
                   (
                       id
                   )
                       )
                   ''')

    # Таблица типов продукции
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS ProductTypes
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       coefficient
                       REAL
                       NOT
                       NULL
                   )
                   ''')

    # Таблица продукции
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS Products
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       article
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       min_partner_price
                       REAL
                       NOT
                       NULL,
                       type_id
                       INTEGER,
                       FOREIGN
                       KEY
                   (
                       type_id
                   ) REFERENCES ProductTypes
                   (
                       id
                   )
                       )
                   ''')

    # Таблица связи материалов и продукции
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS ProductMaterials
                   (
                       product_id
                       INTEGER,
                       material_id
                       INTEGER,
                       required_quantity
                       REAL
                       NOT
                       NULL,
                       PRIMARY
                       KEY
                   (
                       product_id,
                       material_id
                   ),
                       FOREIGN KEY
                   (
                       product_id
                   ) REFERENCES Products
                   (
                       id
                   ),
                       FOREIGN KEY
                   (
                       material_id
                   ) REFERENCES Materials
                   (
                       id
                   )
                       )
                   ''')

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_database()