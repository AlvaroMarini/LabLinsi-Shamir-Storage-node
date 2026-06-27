import { useState, useRef } from 'react'

const buf2hex = (buffer) => [...new Uint8Array(buffer)].map(x => x.toString(16).padStart(2, '0')).join('')
const hex2buf = (hex) => new Uint8Array(hex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)))

function App() {
  const [fileToEncrypt, setFileToEncrypt] = useState(null)
  const [encryptedFile, setEncryptedFile] = useState(null)
  const [ownerId, setOwnerId] = useState('') 
  
  const [statusLeft, setStatusLeft] = useState('')
  const [statusRight, setStatusRight] = useState('')

  const [isDraggingLeft, setIsDraggingLeft] = useState(false)
  const [isDraggingRight, setIsDraggingRight] = useState(false)
  
  const fileInputLeft = useRef(null)
  const fileInputRight = useRef(null)

  // ==========================================
  // LÓGICA DE CIFRADO Y DISTRIBUCIÓN
  // ==========================================
  const handleEncryptAndSplit = async () => {
    if (!fileToEncrypt || !ownerId) {
      setStatusLeft('Selecciona un archivo e ingresa tu PIN de usuario.')
      return
    }

    try {
      const fileBuffer = await fileToEncrypt.arrayBuffer()
      const aesKey = await window.crypto.subtle.generateKey(
        { name: "AES-GCM", length: 256 }, true, ["encrypt", "decrypt"]
      )
      const iv = window.crypto.getRandomValues(new Uint8Array(12))
      const ciphertext = await window.crypto.subtle.encrypt({ name: "AES-GCM", iv: iv }, aesKey, fileBuffer)

      const secretId = crypto.randomUUID()
      const secretIdBytes = new TextEncoder().encode(secretId)
      const encryptedBlob = new Blob([secretIdBytes, iv, ciphertext], { type: 'application/octet-stream' })
      
      const downloadUrl = URL.createObjectURL(encryptedBlob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = `${fileToEncrypt.name}.enc`
      a.click()
      URL.revokeObjectURL(downloadUrl)

      const rawKey = await window.crypto.subtle.exportKey("raw", aesKey)
      const secretKeyHex = buf2hex(rawKey)

      const response = await fetch('/api/split', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-api-key': import.meta.env.VITE_API_KEY
        },
        body: JSON.stringify({
          secret_id: secretId,
          secret: secretKeyHex, 
          owner_id: ownerId, 
          total_shares: 5, 
          threshold: 3 
        })
      })

      if (!response.ok) throw new Error('Error en la red de nodos')
      
      setStatusLeft(`¡Éxito! Archivo cifrado. Protegido bajo el usuario: ${ownerId}`)
      setFileToEncrypt(null)
      if (fileInputLeft.current) fileInputLeft.current.value = ""

      // Borrar el mensaje de éxito a los 5 segundos
      setTimeout(() => {
        setStatusLeft(prevStatus => prevStatus.includes('¡Éxito!') ? '' : prevStatus)
      }, 5000)

    } catch (err) {
      setStatusLeft(`Error: ${err.message}`)
    }
  }

  // ==========================================
  // LÓGICA DE RECUPERACIÓN Y DESCIFRADO
  // ==========================================
  const handleRecoverAndDecrypt = async () => {
    if (!encryptedFile || !ownerId) {
      setStatusRight('Sube el archivo .enc e ingresa el PIN dueño del archivo.')
      return
    }

    try {
      const fileBuffer = await encryptedFile.arrayBuffer()
      const secretIdBytes = fileBuffer.slice(0, 36)
      const secretId = new TextDecoder().decode(secretIdBytes)
      const iv = fileBuffer.slice(36, 48)
      const ciphertext = fileBuffer.slice(48)

      const response = await fetch(`/api/recover/${secretId}?owner_id=${encodeURIComponent(ownerId)}`, {
        method: 'GET',
        headers: { 'x-api-key': import.meta.env.VITE_API_KEY }
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Las bóvedas denegaron el acceso. Usuario incorrecto.');
      }

      const data = await response.json()
      const recoveredHexKey = data.secret 

      const rawKeyBuffer = hex2buf(recoveredHexKey)
      const aesKey = await window.crypto.subtle.importKey(
        "raw", rawKeyBuffer, { name: "AES-GCM", length: 256 }, true, ["encrypt", "decrypt"]
      )

      const decryptedBuffer = await window.crypto.subtle.decrypt(
        { name: "AES-GCM", iv: iv }, aesKey, ciphertext
      )

      const originalName = encryptedFile.name.replace('.enc', '')
      const decryptedBlob = new Blob([decryptedBuffer])
      const downloadUrl = URL.createObjectURL(decryptedBlob)
      const a = document.createElement('a')
      a.href = downloadUrl
      a.download = originalName || 'archivo_recuperado.bin'
      a.click()
      
      setTimeout(() => {
        setStatusRight('¡Éxito! Archivo descifrado y descargado.')
        setEncryptedFile(null)
        if (fileInputRight.current) fileInputRight.current.value = ""
        URL.revokeObjectURL(downloadUrl)

        // Borrar el mensaje de éxito a los 5 segundos
        setTimeout(() => {
          setStatusRight(prevStatus => prevStatus.includes('¡Éxito!') ? '' : prevStatus)
        }, 5000)

      }, 150)

    } catch (err) {
      setStatusRight(`Bloqueo de Seguridad: ${err.message}`)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8 font-sans">
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold text-blue-400 mb-2">Shamir Storage Node</h1>
        <p className="text-slate-400">Plataforma Zero Trust - Cifrado AES-256 + IAM</p>
      </header>

      <div className="max-w-md mx-auto mb-10 bg-slate-800 p-4 rounded-lg border border-slate-600 shadow-md">
        <label className="block text-sm font-semibold text-slate-200 mb-2 text-center">
          Identidad / PIN de Seguridad
        </label>
        <input 
          type="text" 
          value={ownerId}
          onChange={(e) => setOwnerId(e.target.value)}
          placeholder="Ej: lab_linsi"
          className="w-full p-2 bg-slate-900 border border-slate-700 rounded text-slate-200 text-center focus:outline-none focus:border-blue-500 transition-colors"
        />
        <p className="text-xs text-slate-400 mt-2 text-center">Este ID es necesario tanto para cifrar como para recuperar.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
        {/* PANEL IZQUIERDO: CIFRAR */}
        <div className="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700 flex flex-col">
          <h2 className="text-2xl font-semibold mb-4 text-emerald-400">1. Cifrar y Distribuir</h2>
          
          <div 
            onDragOver={(e) => { e.preventDefault(); setIsDraggingLeft(true); }}
            onDragLeave={() => setIsDraggingLeft(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDraggingLeft(false);
              if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                setFileToEncrypt(e.dataTransfer.files[0]);
                if (fileInputLeft.current) fileInputLeft.current.files = e.dataTransfer.files;
              }
            }}
            className={`mb-6 p-6 border-2 border-dashed rounded-lg transition-all text-center grow flex flex-col justify-center items-center gap-3 ${
              isDraggingLeft ? 'border-emerald-400 bg-emerald-900/30' : 'border-slate-600 hover:border-slate-500'
            }`}
          >
            <input 
              type="file" 
              ref={fileInputLeft}
              onChange={(e) => setFileToEncrypt(e.target.files[0])}
              className="w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-emerald-900 file:text-emerald-300 hover:file:bg-emerald-800 cursor-pointer"
            />
            <p className="text-sm text-slate-400 pointer-events-none">O arrastra tu archivo original aquí</p>
          </div>

          <button 
            onClick={handleEncryptAndSplit}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 px-4 rounded transition-colors shadow-[0_0_15px_rgba(16,185,129,0.3)] mt-auto"
          >
            Cifrar Localmente y Proteger Clave
          </button>
          
          <div className="mt-4 min-h-12">
            {statusLeft && <div className="p-3 bg-slate-900 border border-slate-700 rounded text-sm text-slate-300">{statusLeft}</div>}
          </div>
        </div>

        {/* PANEL DERECHO: DESCIFRAR */}
        <div className="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700 flex flex-col">
          <h2 className="text-2xl font-semibold mb-4 text-purple-400">2. Reconstruir y Descifrar</h2>
          
          <div 
            onDragOver={(e) => { e.preventDefault(); setIsDraggingRight(true); }}
            onDragLeave={() => setIsDraggingRight(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDraggingRight(false);
              if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                setEncryptedFile(e.dataTransfer.files[0]);
                if (fileInputRight.current) fileInputRight.current.files = e.dataTransfer.files;
              }
            }}
            className={`mb-6 p-6 border-2 border-dashed rounded-lg transition-all text-center grow flex flex-col justify-center items-center gap-3 ${
              isDraggingRight ? 'border-purple-400 bg-purple-900/30' : 'border-slate-600 hover:border-slate-500'
            }`}
          >
            <input 
              type="file" 
              accept=".enc"
              ref={fileInputRight}
              onChange={(e) => setEncryptedFile(e.target.files[0])}
              className="w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-900 file:text-purple-300 hover:file:bg-purple-800 cursor-pointer"
            />
            <p className="text-sm text-slate-400 pointer-events-none">O arrastra tu archivo .enc aquí</p>
          </div>

          <button 
            onClick={handleRecoverAndDecrypt}
            className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 px-4 rounded transition-colors shadow-[0_0_15px_rgba(168,85,247,0.3)] mt-auto"
          >
            Consultar Clave y Descifrar Archivo
          </button>
          
          <div className="mt-4 min-h-12">
            {statusRight && <div className="p-3 bg-slate-900 border border-slate-700 rounded text-sm text-slate-300">{statusRight}</div>}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App