from database import get_connection

connection = get_connection()

print("Connected successfully!")

connection.close()