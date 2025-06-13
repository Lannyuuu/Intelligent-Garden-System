import sqlite3
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def load_sensor_data(db_path='garden_sensor_data.db', seq_length=10):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT Humidity, DroughtAlert, Light, PH, Rain, CO2 
        FROM SensorData 
        ORDER BY Timestamp DESC 
        LIMIT ?
    ''', (seq_length * 100,))
    
    data = cursor.fetchall()
    conn.close()
    
    if not data:
        raise ValueError("No sensor data found in database")
    
    data_array = np.array(data, dtype=np.float32)
    scaler = MinMaxScaler()
    normalized_data = scaler.fit_transform(data_array)
    
    # create sequence data while maintaining the time dimension
    sequences = []
    for i in range(len(normalized_data) - seq_length):
        sequences.append(normalized_data[i:i+seq_length])
    
    sequences = np.array(sequences)
    print(f"Data shape: {sequences.shape}")  
    
    return sequences, scaler