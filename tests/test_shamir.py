import pytest
from src.domain.shamir import ShamirScheme

def test_secret_is_recoverable_with_k_shares():
    shamir = ShamirScheme(total_shares=5, threshold=3)
    secret_original = b"mensaje_super_secreto"
    
    # Dividimos
    shares = shamir.split_secret(secret_original)
    
    # Tomamos solo 3 fragmentos (el umbral exacto)
    selected_shares = shares[:3]
    
    # Verificamos
    secret_recuperado = shamir.recover_secret(selected_shares)
    assert secret_recuperado == secret_original

def test_secret_fails_with_less_than_k_shares():
    shamir = ShamirScheme(total_shares=5, threshold=3)
    shares = shamir.split_secret(b"secreto")
    
    # Intentamos recuperar con 2 fragmentos (debería fallar)
    with pytest.raises(ValueError):
        shamir.recover_secret(shares[:2])