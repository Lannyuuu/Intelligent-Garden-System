import torch
import numpy as np
from .model import VAE  

class VAESensorGenerator:
    def __init__(self, model_path='vae_model.pth'):
        checkpoint = torch.load(model_path, map_location=torch.device('cpu'), weights_only=False)
        self.seq_length = checkpoint['seq_length']
        self.scaler = checkpoint['scaler']
        
        # Number of sensor features
        input_dim = 6  
        self.model = VAE(input_dim=input_dim, 
                         seq_length=self.seq_length, 
                         latent_dim=8)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        # Initialize history buffer
        self.history = np.zeros((self.seq_length, 6))

    def update_history(self, new_data):
        """Update the history buffer with new data by shifting and appending"""
        self.history = np.roll(self.history, shift=-1, axis=0)
        self.history[-1] = new_data

    def generate(self):
        """Generate new sensor data using the VAE model"""
        # Prepare input sequence
        input_seq = self.history.copy()
        normalized_seq = self.scaler.transform(input_seq)
        
        # Generate new data
        with torch.no_grad():
            tensor_seq = torch.tensor(normalized_seq, dtype=torch.float32).unsqueeze(0)  # Add batch dimension
            recon_seq, _, _ = self.model(tensor_seq)
        
        # Post-processing
        generated = recon_seq.squeeze(0).numpy()  
        generated = self.scaler.inverse_transform(generated)
        
        # Extract latest timestep and update history
        new_data = generated[-1]
        self.update_history(new_data)
        
        # Process boolean fields
        drought_alert = bool(new_data[1] > 0.5)
        rain = bool(new_data[4] > 0.5)
        
        return {
            'humidity': float(max(0, min(100, new_data[0]))),
            'drought_alert': drought_alert,
            'light': float(max(0, new_data[2])),
            'ph': float(max(0, min(14, new_data[3]))),
            'rain': rain,
            'co2': float(max(300, new_data[5]))
        }