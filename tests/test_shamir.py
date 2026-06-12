import pytest
from src.domain.shamir import ShamirScheme

def test_secret_is_recoverable_with_k_shares():
    shamir = ShamirScheme(total_shares=5, threshold=3)
    secret_original = b"mensaje_super_secreto"
    
    shares = shamir.split_secret(secret_original)
    selected_shares = shares[:3]
    
    secret_recuperado = shamir.recover_secret(selected_shares)
    assert secret_recuperado == secret_original

def test_secret_fails_with_less_than_k_shares():
    shamir = ShamirScheme(total_shares=5, threshold=3)
    shares = shamir.split_secret(b"secreto")
    
    with pytest.raises(ValueError):
        shamir.recover_secret(shares[:2])

def test_corrupted_share_is_ignored():
    shamir = ShamirScheme(total_shares=5, threshold=3)
    secret_original = b"secreto_blindado"
    shares = shamir.split_secret(secret_original)
    
    # Tomamos 4 fragmentos (necesitamos 3, así que tenemos margen de error)
    selected_shares = shares[:4]
    
    # Corrompemos intencionalmente el primer fragmento (simulando un ataque o falla de disco)
    x, y_bytes, hash_val = selected_shares[0]
    corrupted_y = (int.from_bytes(y_bytes, "big") + 1).to_bytes(70, "big")
    selected_shares[0] = (x, corrupted_y, hash_val) # El hash ya no coincide con la nueva 'y'
    
    # Como le pasamos 4 fragmentos, ignorará el corrupto, usará los 3 limpios y funcionará
    secret_recuperado = shamir.recover_secret(selected_shares)
    assert secret_recuperado == secret_original