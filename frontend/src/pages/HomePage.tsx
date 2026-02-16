import Tagline from '../components/Tagline';
import DocumentUpload from '../components/DocumentUpload';

export default function HomePage() {
  return (
    <div className="app">
      <header className="app-header">
        <p className="app-title">SignalDrift</p>
        <Tagline />
      </header>
      <main className="app-main">
        <DocumentUpload />
      </main>
    </div>
  );
}
