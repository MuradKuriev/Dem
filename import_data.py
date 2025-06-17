import pandas as pd
import sqlite3


def import_data():
    conn = sqlite3.connect('obraz_plus.db')
    cursor = conn.cursor()

    # Create tables if they don't exist (in correct order)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS MaterialTypes
                   (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       loss_percentage REAL NOT NULL
                   )
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS Materials
                   (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       type_id INTEGER,
                       unit_price REAL NOT NULL CHECK (unit_price >= 0),
                       stock_quantity REAL NOT NULL,
                       min_quantity REAL NOT NULL CHECK (min_quantity >= 0),
                       package_quantity REAL NOT NULL,
                       unit_of_measure TEXT NOT NULL,
                       FOREIGN KEY (type_id) REFERENCES MaterialTypes (id)
                   )
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS ProductTypes
                   (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       coefficient REAL NOT NULL
                   )
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS Products
                   (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL,
                       article TEXT NOT NULL UNIQUE,
                       min_partner_price REAL NOT NULL,
                       type_id INTEGER,
                       FOREIGN KEY (type_id) REFERENCES ProductTypes (id)
                   )
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS ProductMaterials
                   (
                       product_id INTEGER,
                       material_id INTEGER,
                       required_quantity REAL NOT NULL,
                       PRIMARY KEY (product_id, material_id),
                       FOREIGN KEY (product_id) REFERENCES Products (id),
                       FOREIGN KEY (material_id) REFERENCES Materials (id)
                   )
                   """)

    # Clear tables in correct order
    cursor.execute("DELETE FROM ProductMaterials")
    cursor.execute("DELETE FROM Products")
    cursor.execute("DELETE FROM Materials")
    cursor.execute("DELETE FROM ProductTypes")
    cursor.execute("DELETE FROM MaterialTypes")
    conn.commit()



    conn.close()


if __name__ == "__main__":
    import_data()