import sqlite3
 
def create_table():
    
    conn = sqlite3.connect('garden_sensor_data.db')
    cursor = conn.cursor()
 
    # create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SensorData (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Timestamp TEXT NOT NULL,
            Humidity REAL NOT NULL,
            DroughtAlert INTEGER NOT NULL,
            Light INTEGER NOT NULL,
            PH REAL NOT NULL,
            Rain INTEGER NOT NULL,
            CO2 REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
 
if __name__ == '__main__':
    create_table()
    print("Table SensorData created successfully.")
