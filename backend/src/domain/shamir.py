import random
import hashlib

PRIME = 2**521 - 1

class ShamirScheme:
    def __init__(self, total_shares: int, threshold: int):
        if threshold > total_shares:
            raise ValueError("El umbral (k) no puede ser mayor a los fragmentos (n).")
        self.n = total_shares
        self.k = threshold

    # Función auxiliar para generar el hash de un fragmento
    def _generate_hash(self, x: int, y_bytes: bytes) -> str:
        # Hasheamos la combinación de la posición (x) y el valor (y)
        data = f"{x}:{y_bytes.hex()}".encode('utf-8')
        return hashlib.sha256(data).hexdigest()

    def split_secret(self, secret: bytes) -> list[tuple[int, bytes, str]]:
        secret_int = int.from_bytes(secret, byteorder="big")
        if secret_int >= PRIME:
            raise ValueError("El secreto es demasiado grande.")
            
        coeficientes = [secret_int] + [random.randint(1, PRIME - 1) for _ in range(self.k - 1)]
        shares = []
        
        for x in range(1, self.n + 1):
            y = 0
            for i, coef in enumerate(coeficientes):
                y = (y + coef * (x ** i)) % PRIME
                
            y_bytes = y.to_bytes(70, byteorder="big")
            
            # --- MEJORA DEL PROFESOR: Agregamos el Hash de Integridad ---
            fragment_hash = self._generate_hash(x, y_bytes)
            
            # Ahora devolvemos una tupla de 3 elementos: (x, y, hash)
            shares.append((x, y_bytes, fragment_hash))
            
        return shares

    def recover_secret(self, shares: list[tuple[int, bytes, str]]) -> bytes:
        valid_shares = []
        
        # --- MEJORA DEL PROFESOR: Validación antes de la interpolación ---
        for x, y_bytes, provided_hash in shares:
            expected_hash = self._generate_hash(x, y_bytes)
            if expected_hash != provided_hash:
                # Si el hash no coincide, ignoramos este fragmento corrupto
                continue 
            valid_shares.append((x, y_bytes))
            
            # Si ya juntamos suficientes fragmentos válidos, dejamos de verificar
            if len(valid_shares) == self.k:
                break

        if len(valid_shares) < self.k:
            raise ValueError("No hay suficientes fragmentos válidos e íntegros para alcanzar el umbral.")
        
        # Interpolación de Lagrange clásica con los fragmentos limpios
        secret_int = 0
        for i, (x_i, y_bytes) in enumerate(valid_shares):
            y_i = int.from_bytes(y_bytes, byteorder="big")
            numerador = 1
            denominador = 1
            
            for j, (x_j, _) in enumerate(valid_shares):
                if i != j:
                    numerador = (numerador * (0 - x_j)) % PRIME
                    denominador = (denominador * (x_i - x_j)) % PRIME
                    
            inv_denominador = pow(denominador, PRIME - 2, PRIME)
            termino = (y_i * numerador * inv_denominador) % PRIME
            secret_int = (secret_int + termino) % PRIME
            
        byte_length = (secret_int.bit_length() + 7) // 8
        return secret_int.to_bytes(byte_length, byteorder="big")