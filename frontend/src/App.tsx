import HelloWorld from './components/HelloWorld';
import DocumentUpload from './components/DocumentUpload';
import './App.css';

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <p className="app-title">SignalDrift</p>
        <HelloWorld />
      </header>
      <main className="app-main">
        <DocumentUpload />
      </main>
    </div>
  );
}

export default App;
