import { AuthProvider } from './context/AuthContext';
// import { CategoriasProvider } from './context/CategoriasContext';
import Routing from './routes/Routing';
import AvisoServidor from './components/AvisoServidor/AvisoServidor';

function App() {
  return (
    <AuthProvider>
      {/* <CategoriasProvider> */}
        <div>
          <AvisoServidor/>
          <Routing/>
        </div>
      {/* </CategoriasProvider> */}
    </AuthProvider>
  )
}

export default App