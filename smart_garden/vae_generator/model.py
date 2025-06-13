import torch
import torch.nn as nn

class VAE(nn.Module):
    def __init__(self, input_dim, seq_length, latent_dim=8):
        super(VAE, self).__init__()
        self.input_dim = input_dim
        self.seq_length = seq_length
        self.latent_dim = latent_dim
        
        # Encoder - for processing sequential data
        self.encoder = nn.Sequential(
            nn.Flatten(start_dim=1),  
            nn.Linear(input_dim * seq_length, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU()
        )
        
        # Latent space mean and log variance
        self.fc_mu = nn.Linear(16, latent_dim)
        self.fc_logvar = nn.Linear(16, latent_dim)
        
        # Decoder - for reconstructing sequential data
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim * seq_length),
            nn.Sigmoid()
        )

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def forward(self, x):
        # x shape: [batch_size, seq_length, input_dim]
        
        # Encoding
        h = self.encoder(x)  # Flatten and encode
        mu, logvar = self.fc_mu(h), self.fc_logvar(h)
        
        # Reparameterization
        z = self.reparameterize(mu, logvar)
        
        # Decoding
        x_recon = self.decoder(z)
        x_recon = x_recon.view(-1, self.seq_length, self.input_dim)  # Reshape to sequential format
        
        return x_recon, mu, logvar

# Loss function
def vae_loss(recon_x, x, mu, logvar):
    # Need to adjust loss calculation for sequential data
    # First flatten recon_x and x
    recon_x = recon_x.view(recon_x.size(0), -1)
    x = x.view(x.size(0), -1)
    
    BCE = nn.functional.binary_cross_entropy(recon_x, x, reduction='sum')
    KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    return BCE + KLD