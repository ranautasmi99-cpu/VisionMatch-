import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "216CI119@ar"),
    "database": os.getenv("DB_NAME", "visionmatch")
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

def get_user_by_email(email):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM users WHERE email = %s LIMIT 1"
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user

def get_user_by_id(user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM users WHERE id = %s LIMIT 1"
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user

def insert_user(name, email, password_hash):
    connection = get_connection()
    cursor = connection.cursor()
    query = "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)"
    cursor.execute(query, (name, email, password_hash))
    connection.commit()
    user_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return user_id

def block_user(blocker_id, blocked_id):
    connection = get_connection()
    cursor = connection.cursor()
    # Use IGNORE to avoid duplicate key errors if already blocked
    query = "INSERT IGNORE INTO blocked_users (blocker_id, blocked_id) VALUES (%s, %s)"
    cursor.execute(query, (blocker_id, blocked_id))
    connection.commit()
    cursor.close()
    connection.close()

def is_blocked(user_a, user_b):
    """Returns True if either user has blocked the other"""
    connection = get_connection()
    cursor = connection.cursor()
    query = "SELECT id FROM blocked_users WHERE (blocker_id = %s AND blocked_id = %s) OR (blocker_id = %s AND blocked_id = %s) LIMIT 1"
    cursor.execute(query, (user_a, user_b, user_b, user_a))
    blocked = cursor.fetchone() is not None
    cursor.close()
    connection.close()
    return blocked

def insert_item(
    name,
    description,
    category,
    status,
    image_path,
    location,
    item_date,
    user_id
):
    image_path = image_path.replace("\\", "/")
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO items
        (name, description, category, status,
         image_path, location, item_date, user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        name,
        description,
        category,
        status,
        image_path,
        location,
        item_date,
        user_id
    )

    cursor.execute(query, values)

    connection.commit()

    item_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return item_id
def get_conversation(item_id, user_a_id, user_b_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    # user_a and user_b could be in either order in DB
    query = """
        SELECT * FROM conversations
        WHERE item_id = %s AND (
            (user_a_id = %s AND user_b_id = %s) OR
            (user_a_id = %s AND user_b_id = %s)
        ) LIMIT 1
    """
    cursor.execute(query, (item_id, user_a_id, user_b_id, user_b_id, user_a_id))
    conv = cursor.fetchone()
    cursor.close()
    connection.close()
    return conv

def get_conversation_by_id(conversation_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM conversations WHERE id = %s LIMIT 1"
    cursor.execute(query, (conversation_id,))
    conv = cursor.fetchone()
    cursor.close()
    connection.close()
    return conv

def create_conversation(item_id, user_a_id, user_b_id):
    connection = get_connection()
    cursor = connection.cursor()
    query = "INSERT INTO conversations (item_id, user_a_id, user_b_id) VALUES (%s, %s, %s)"
    cursor.execute(query, (item_id, user_a_id, user_b_id))
    connection.commit()
    conv_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return conv_id

def get_user_conversations(user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT c.*, i.name as item_name,
        CASE WHEN c.user_a_id = %s THEN u_b.name ELSE u_a.name END as other_user_name,
        (SELECT message_text FROM messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) as last_message,
        (SELECT created_at FROM messages WHERE conversation_id = c.id ORDER BY created_at DESC LIMIT 1) as last_message_time
        FROM conversations c
        JOIN items i ON c.item_id = i.id
        JOIN users u_a ON c.user_a_id = u_a.id
        JOIN users u_b ON c.user_b_id = u_b.id
        WHERE c.user_a_id = %s OR c.user_b_id = %s
        ORDER BY last_message_time DESC
    """
    cursor.execute(query, (user_id, user_id, user_id))
    convs = cursor.fetchall()
    cursor.close()
    connection.close()
    return convs

def insert_message(conversation_id, sender_id, text):
    connection = get_connection()
    cursor = connection.cursor()
    query = "INSERT INTO messages (conversation_id, sender_id, message_text) VALUES (%s, %s, %s)"
    cursor.execute(query, (conversation_id, sender_id, text))
    connection.commit()
    msg_id = cursor.lastrowid
    cursor.close()
    connection.close()
    return msg_id

def get_messages(conversation_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT m.*, u.name as sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.conversation_id = %s
        ORDER BY m.created_at ASC
    """
    cursor.execute(query, (conversation_id,))
    msgs = cursor.fetchall()
    cursor.close()
    connection.close()
    return msgs

def create_notification(user_id, type, text, link):
    connection = get_connection()
    cursor = connection.cursor()
    query = "INSERT INTO notifications (user_id, type, text, link) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (user_id, type, text, link))
    connection.commit()
    cursor.close()
    connection.close()

def get_user_notifications(user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC"
    cursor.execute(query, (user_id,))
    notifs = cursor.fetchall()
    cursor.close()
    connection.close()
    return notifs

def get_unread_notification_count(user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = FALSE"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result['count'] if result else 0

def mark_notification_read(notif_id, user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    # Check ownership and get link
    query = "SELECT link FROM notifications WHERE id = %s AND user_id = %s"
    cursor.execute(query, (notif_id, user_id))
    notif = cursor.fetchone()
    if notif:
        update_query = "UPDATE notifications SET is_read = TRUE WHERE id = %s"
        cursor.execute(update_query, (notif_id,))
        connection.commit()
    cursor.close()
    connection.close()
    return notif['link'] if notif else None

def get_item_by_id(item_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT * FROM items WHERE id = %s LIMIT 1"
    cursor.execute(query, (item_id,))
    item = cursor.fetchone()
    cursor.close()
    connection.close()
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