import { Outlet, NavLink } from 'react-router-dom';

function App() {
  const navLinkClass = ({ isActive }) =>
    `text-lg font-medium transition-colors ${
      isActive ? 'text-teal-400 border-b-2 border-teal-400' : 'text-gray-400 hover:text-white'
    }`;
    
  return (
    <div className="min-h-screen bg-[#1a1a1b] p-4 sm:p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-teal-400">Kuroba Web (BFF)</h1>
        <p className="text-sm text-gray-400 mb-4">Offline-first Imageboard Archive Client</p>
        <nav className="flex space-x-6 text-lg border-b border-gray-700 pb-2">
          <NavLink to="/" className={navLinkClass} end>
            Imageboard Archive
          </NavLink>
          <NavLink to="/dashboard" className={navLinkClass}>
            Dashboard
          </NavLink>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}

export default App;

