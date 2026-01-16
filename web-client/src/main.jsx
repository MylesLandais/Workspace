import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App.jsx'
import ThreadList from './components/ThreadList.jsx'
import ThreadView from './components/ThreadView.jsx'
import Dashboard from './components/Dashboard.jsx' // New Import
import './index.css'
import 'gridstack/dist/gridstack.min.css'; // Added Gridstack CSS here

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<ThreadList />} />
          <Route path="thread/:board/:threadId" element={<ThreadView />} />
          {/* Removed /feed route */}
          <Route path="dashboard" element={<Dashboard />} /> {/* New Dashboard Route */}
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
