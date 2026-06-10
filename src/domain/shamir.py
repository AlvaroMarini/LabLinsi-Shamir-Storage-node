import random

# Usamos el 13º número primo de Mersenne (2^521 - 1) para nuestro Campo Finito.
# Es un número gigante que nos permite cifrar mensajes de hasta ~65 bytes de largo.
PRIME = 2**521 - 1

class ShamirScheme:
    def __init__(self, total_shares: int, threshold: int):
        if threshold > total_shares:
            raise ValueError("El umbral (k) no puede ser mayor a los fragmentos (n).")
        self.n = total_shares
        self.k = threshold

    def split_secret(self, secret: bytes) -> list[tuple[int, bytes]]:
        # 1. Convertimos el mensaje (bytes) a un único número entero gigante
        secret_int = int.from_bytes(secret, byteorder="big")
        
        if secret_int >= PRIME:
            raise ValueError("El secreto es demasiado grande para la Prueba de Concepto.")
            
        # 2. Generamos el polinomio: a_0 es el secreto, los demás son aleatorios
        coeficientes = [secret_int] + [random.randint(1, PRIME - 1) for _ in range(self.k - 1)]
        
        shares = []
        for x in range(1, self.n + 1):
            # 3. Evaluamos el polinomio (y = a_0 + a_1*x + a_2*x^2 ... mod PRIME)
            y = 0
            for i, coef in enumerate(coeficientes):
                y = (y + coef * (x ** i)) % PRIME
                
            # Convertimos 'y' a bytes (usamos 70 bytes de longitud para asegurar que entre)
            shares.append((x, y.to_bytes(70, byteorder="big")))
            
        return shares

    def recover_secret(self, shares: list[tuple[int, bytes]]) -> bytes:
        if len(shares) < self.k:
            raise ValueError("No hay suficientes fragmentos para alcanzar el umbral.")
        
        # Tomamos exactamente 'k' fragmentos
        k_shares = shares[:self.k]
        secret_int = 0
        
        # 4. Interpolación de Lagrange en x = 0
        for i, (x_i, y_bytes) in enumerate(k_shares):
            y_i = int.from_bytes(y_bytes, byteorder="big")
            numerador = 1
            denominador = 1
            
            for j, (x_j, _) in enumerate(k_shares):
                if i != j:
                    numerador = (numerador * (0 - x_j)) % PRIME
                    denominador = (denominador * (x_i - x_j)) % PRIME
                    
            # Calculamos el inverso modular usando el Pequeño Teorema de Fermat
            inv_denominador = pow(denominador, PRIME - 2, PRIME)
            termino = (y_i * numerador * inv_denominador) % PRIME
            secret_int = (secret_int + termino) % PRIME
            
        # 5. Convertimos el entero matemático de vuelta al texto original (bytes)
        byte_length = (secret_int.bit_length() + 7) // 8
        return secret_int.to_bytes(byte_length, byteorder="big")