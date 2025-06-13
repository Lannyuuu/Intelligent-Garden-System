import torch
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from vae_generator.model import VAE, vae_loss
from vae_generator.data_loader import load_sensor_data

def train_vae():
    input_dim = 6
    seq_length = 10
    latent_dim = 8
    batch_size = 32
    epochs = 100
    
    sequences, scaler = load_sensor_data(seq_length=seq_length)
    print(f"Data shape: {sequences.shape}")  # (990, 10, 6)
    
    dataset = torch.utils.data.TensorDataset(torch.tensor(sequences, dtype=torch.float32))
    
    # Ensure total number of samples is divisible by batch_size (truncate excess data)
    num_samples = len(dataset)
    num_batches = num_samples // batch_size
    if num_batches * batch_size < num_samples:
        dataset = torch.utils.data.Subset(dataset, range(num_batches * batch_size))
    
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # Initialize model
    model = VAE(input_dim=input_dim, seq_length=seq_length, latent_dim=latent_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    # Training loop
    for epoch in range(epochs):
        for batch in dataloader:
            data = batch[0]  # Get the input data from the batch
            
            optimizer.zero_grad()
            recon_batch, mu, logvar = model(data)
            loss = vae_loss(recon_batch, data, mu, logvar)
            
            loss.backward()
            optimizer.step()
        
        print(f'Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}')
    
    # Save trained model
    torch.save({
        'model_state_dict': model.state_dict(),
        'scaler': scaler,
        'seq_length': seq_length
    }, 'vae_model.pth')
    print("VAE model trained and saved")
    
if __name__ == '__main__':
    train_vae()