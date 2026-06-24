import { useState } from 'react'

function App() {
  const [secretToSplit, setSecretToSplit] = useState('')
  const [generatedShares, setGeneratedShares] = useState([])
  const [splitError, setSplitError] = useState('')

  const [recoveredSecret, setRecoveredSecret] = useState('')
  const [recoverError, setRecoverError] = useState('')

  const handleSplit = async () => {
    try {
      setSplitError('')
      const response = await fetch('/api/split', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-api-key': import.meta.env.VITE_API_KEY
        },
        body: JSON.stringify({ secret: secretToSplit, total_shares: 5, threshold: 3 })
      })
      
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Error al fraccionar')
      
      setGeneratedShares(data.shares)
    } catch (err) {
      setSplitError(err.message)
    }
  }

  const handleRecover = async () => {
    try {
      setRecoverError('')
      setRecoveredSecret('')
      
      // Ahora usamos GET porque el Gateway recolecta los datos de los nodos
      const response = await fetch('/api/recover', {
        method: 'GET',
        headers: { 
          'x-api-key': import.meta.env.VITE_API_KEY
        }
      })
      
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Error al recuperar')
      
      setRecoveredSecret(data.secret)
    } catch (err) {
      setRecoverError(err.message)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8 font-sans">
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold text-blue-400 mb-2">Shamir Storage Node</h1>
        <p className="text-slate-400">Dashboard de Pruebas (PoC) - Criptografía de Umbral y VSS</p>
      </header>

      <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
        
        {/* --- PANEL IZQUIERDO: FRACCIONAR --- */}
        <div className="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700">
          <h2 className="text-2xl font-semibold mb-4 text-emerald-400">1. Fraccionar y Distribuir</h2>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-400 mb-1">Secreto a proteger (máx ~65 chars):</label>
            <input 
              type="text" 
              className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-white focus:outline-none focus:border-emerald-500"
              placeholder="Ej: Clave maestra de la DB"
              value={secretToSplit}
              onChange={(e) => setSecretToSplit(e.target.value)}
            />
          </div>

          <button 
            onClick={handleSplit}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded transition-colors"
          >
            Generar 5 Fragmentos y Enviar a Bóvedas
          </button>

          {splitError && <p className="text-red-400 mt-4 text-sm">{splitError}</p>}

          {generatedShares.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-slate-300 mb-2">Fragmentos distribuidos en la red (JSON):</h3>
              <pre className="bg-slate-900 p-4 rounded text-xs text-emerald-300 overflow-x-auto border border-slate-700">
                {JSON.stringify(generatedShares, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* --- PANEL DERECHO: RECUPERAR --- */}
        <div className="bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-700">
          <h2 className="text-2xl font-semibold mb-4 text-purple-400">2. Recuperar Secreto</h2>
          
          <div className="mb-4">
            <p className="text-sm text-slate-400">
              El Gateway consultará de forma asíncrona a los contenedores aislados en la red Zero Trust. Si al menos 3 nodos responden con fragmentos íntegros, el secreto será reconstruido.
            </p>
          </div>

          <button 
            onClick={handleRecover}
            className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-2 px-4 rounded transition-colors"
          >
            Consultar Nodos e Interpolar
          </button>

          {recoverError && <p className="text-red-400 mt-4 text-sm font-semibold">{recoverError}</p>}

          {recoveredSecret && (
            <div className="mt-6 p-4 bg-emerald-900 border border-emerald-500 rounded text-center">
              <h3 className="text-sm font-semibold text-emerald-200 mb-1">Secreto Original:</h3>
              <p className="text-xl font-bold text-white">{recoveredSecret}</p>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}

export default App