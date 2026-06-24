import { useState, useRef } from 'react'

// --- FUNCIONES AUXILIARES PARA CRIPTOGRAFÍA ---
const buf2hex = (buffer) => [...new Uint8Array(buffer)].map(x => x.toString(16).padStart(2, '0')).join('')
const hex2buf = (hex) => new Uint8Array(hex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)))

function App() {
  // Estados UI
  const [fileToEncrypt, setFileToEncrypt] = useState(null)
  const [encryptedFile, setEncryptedFile] = useState(null)
  const [statusLeft, setStatusLeft] = useState('')
  const [statusRight, setStatusRight] = useState('')
  
  const fileInputLeft = useRef(null)
  const fileInputRight = useRef(null)

  // ==========================================
  // FASE 3: CIFRADO LOCAL Y DISTRIBUCIÓN
  // ==========================================
  const handleEncryptAndSplit = async () => {
    if (!fileToEncrypt) {
      setStatusLeft('Por favor selecciona un archivo primero.')
      return
    }

    try {
      setStatusLeft('Generando clave AES y cifrando archivo localmente...')
      
      // 1. Leer el archivo como ArrayBuffer
      const fileBuffer = await fileToEncrypt.arrayBuffer()

      // 2. Generar llave AES-256-GCM
      const aesKey = await window.crypto.subtle.generateKey(
        { name: "AES-GCM", length: 256 },
        true, // Permite exportar la llave
        ["encrypt", "decrypt"]
      )

      // 3. Crear un Vector de Inicialización (IV) aleatorio (necesario para GCM)
      const iv = window.crypto.getRandomValues(new Uint8Array(12))

      // 4. Cifrar el archivo
      const ciphertext = await window.crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        aesKey,
        fileBuffer
      )

      const secretId = crypto.randomUUID()
      const secretIdBytes = new TextEncoder().encode(secretId)

      // 5. Empaquetar el IV junto con el archivo cifrado para poder descifrarlo después
      const encryptedBlob = new Blob([secretIdBytes, iv, ciphertext], { type: 'application/octet-stream' })
      
      // 6. Descargar el archivo cifrado (.enc) simulando almacenamiento local
      const downloadUrl = URL.createObjectURL(encryptedBlob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `${fileToEncrypt.name}.enc`
      a.click()
      URL.revokeObjectURL(downloadUrl)

      // 7. Exportar la llave AES a formato Hexadecimal para enviarla a Shamir
      const rawKey = await window.crypto.subtle.exportKey("raw", aesKey)
      const secretKeyHex = buf2hex(rawKey)

      setStatusLeft('Clave generada. Enviando al Gateway para fragmentación...')

      // 8. Enviar SOLAMENTE la llave a nuestra API Python (Zero Trust)
      const response = await fetch('/api/split', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-api-key': import.meta.env.VITE_API_KEY
        },
        body: JSON.stringify({
          secret_id: secretId,
          secret: secretKeyHex, 
          total_shares: 5, 
          threshold: 3 
        })
      })

      if (!response.ok) throw new Error('Error al fragmentar en la red de nodos')
      
      setStatusLeft(`¡Éxito! Archivo cifrado descargado y clave AES distribuida en 5 bóvedas.`)
      setFileToEncrypt(null)
      fileInputLeft.current.value = ""

    } catch (err) {
      setStatusLeft(`Error: ${err.message}`)
    }
  }

  // ==========================================
  // FASE 4: RECOLECCIÓN Y DESCIFRADO LOCAL
  // ==========================================
  const handleRecoverAndDecrypt = async () => {
    if (!encryptedFile) {
      setStatusRight('Por favor selecciona el archivo .enc primero.')
      return
    }

    try {
      setStatusRight('Leyendo archivo e identificando UUID...')

      // 1. Leer el archivo subido
      const fileBuffer = await encryptedFile.arrayBuffer()
      
      // 2. Extraer el UUID (los primeros 36 bytes)
      const secretIdBytes = fileBuffer.slice(0, 36)
      const secretId = new TextDecoder().decode(secretIdBytes)

      // 3. Extraer el IV (desde el byte 36 al 48)
      const iv = fileBuffer.slice(36, 48)
      
      // 4. Extraer el texto cifrado (desde el byte 48 en adelante)
      const ciphertext = fileBuffer.slice(48)

      setStatusRight(`⏳ Archivo detectado (ID: ${secretId.substring(0,8)}...). Consultando nodos...`)

      // 5. Pedirle al Gateway la llave de ese archivo específico
      const response = await fetch(`/api/recover/${secretId}`, {
        method: 'GET',
        headers: { 'x-api-key': import.meta.env.VITE_API_KEY }
      })
      
      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Nodos insuficientes o error de red.')
      }

      const data = await response.json()
      const recoveredHexKey = data.secret // Esta es nuestra llave AES en texto

      setStatusRight('Clave recuperada. Descifrando archivo localmente...')

      // 6. Reconstruir la llave AES en el navegador
      const rawKeyBuffer = hex2buf(recoveredHexKey)
      const aesKey = await window.crypto.subtle.importKey(
        "raw",
        rawKeyBuffer,
        { name: "AES-GCM", length: 256 },
        true,
        ["encrypt", "decrypt"]
      )

      // 7. Descifrar
      const decryptedBuffer = await window.crypto.subtle.decrypt(
        { name: "AES-GCM", iv: iv },
        aesKey,
        ciphertext
      )

      // 8. Descargar el archivo original restaurado
      const originalName = encryptedFile.name.replace('.enc', '')
      const decryptedBlob = new Blob([decryptedBuffer])
      const downloadUrl = URL.createObjectURL(decryptedBlob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = originalName || 'archivo_recuperado.bin'
      a.click()
      URL.revokeObjectURL(downloadUrl)

      setStatusRight('¡Éxito! Clave reconstruida y archivo original descifrado y descargado.')
      setEncryptedFile(null)
      fileInputRight.current.value = ""

    } catch (err) {
      setStatusRight(`Fallo de seguridad: ${err.message}`)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8 font-sans">
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold text-blue-400 mb-2">Shamir Storage Node</h1>
        <p className="text-slate-400">Plataforma Zero Trust - Cifrado AES-256 + VSS Distribuido</p>
      </header>

      <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
        
        {/* --- PANEL IZQUIERDO: UPLOAD --- */}
        <div className="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700">
          <h2 className="text-2xl font-semibold mb-4 text-emerald-400">1. Cifrar y Distribuir</h2>
          <p className="text-sm text-slate-400 mb-6">El archivo se cifra en tu navegador. Solo la clave generada viaja al clúster para ser fragmentada.</p>
          
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-2">Seleccionar archivo a proteger:</label>
            <input 
              type="file" 
              ref={fileInputLeft}
              onChange={(e) => setFileToEncrypt(e.target.files[0])}
              className="w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-emerald-900 file:text-emerald-300 hover:file:bg-emerald-800"
            />
          </div>

          <button 
            onClick={handleEncryptAndSplit}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 px-4 rounded transition-colors shadow-[0_0_15px_rgba(16,185,129,0.3)]"
          >
            Cifrar Localmente y Proteger Clave
          </button>

          {statusLeft && (
            <div className="mt-4 p-3 bg-slate-900 border border-slate-700 rounded text-sm text-slate-300">
              {statusLeft}
            </div>
          )}
        </div>

        {/* --- PANEL DERECHO: DOWNLOAD --- */}
        <div className="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700">
          <h2 className="text-2xl font-semibold mb-4 text-purple-400">2. Reconstruir y Descifrar</h2>
          <p className="text-sm text-slate-400 mb-6">Se consultará a la red por la clave. Si el umbral de nodos (3/5) es exitoso, se descifrará tu archivo.</p>
          
          <div className="mb-6">
            <label className="block text-sm font-medium text-slate-300 mb-2">Subir archivo bloqueado (.enc):</label>
            <input 
              type="file" 
              accept=".enc"
              ref={fileInputRight}
              onChange={(e) => setEncryptedFile(e.target.files[0])}
              className="w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-900 file:text-purple-300 hover:file:bg-purple-800"
            />
          </div>

          <button 
            onClick={handleRecoverAndDecrypt}
            className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 px-4 rounded transition-colors shadow-[0_0_15px_rgba(168,85,247,0.3)]"
          >
            Consultar Clave y Descifrar Archivo
          </button>

          {statusRight && (
            <div className="mt-4 p-3 bg-slate-900 border border-slate-700 rounded text-sm text-slate-300">
              {statusRight}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}

export default App