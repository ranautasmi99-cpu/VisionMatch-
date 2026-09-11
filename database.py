import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "216CI119@ar"),
    "database": os.getenv("DB_NAME", "visionmatch")
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def insert_item(
    name,
    description,
    category,
    status,
    image_path,
    location,
    item_date
):
    image_path = image_path.replace("\\", "/")
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO items
        (name, description, category, status,
         image_path, location, item_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        name,
        description,
        category,
        status,
        image_path,
        location,
        item_date
    )

    cursor.execute(query, values)

    connection.commit()

    item_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return item_id
def get_item_by_image_path(image_path):

    # Convert Windows "\" path to "/" so it matches the database
    image_path = image_path.replace("\\", "/")

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT *
        FROM items
        WHERE image_path = %s
        LIMIT 1
    """

    cursor.execute(query, (image_path,))

    item = cursor.fetchone()

    cursor.close()
    connection.close()

    return item