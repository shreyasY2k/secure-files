// src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import KeycloakProvider from './components/auth/KeycloakProvider';
import ProtectedRoute from './components/auth/ProtectedRoute';
import SharedFilePage from './components/files/SharedFilePage';
import Dashboard from './components/dashboard/Dashboard';
import Navbar from './components/layout/Navbar';
import LandingPage from './components/layout/LandingPage';
import AdminDashboard from './components/admin/AdminDashboard';
import MFASetup from './components/auth/MFASetup';
import FileView from './components/files/FileView';

function App() {
  return (
    <Provider store={store}>
      <Router>
        <KeycloakProvider>
          <div className="min-h-screen bg-gray-100">
            <Navbar />
            <Routes>
              <Route path="/" element={<LandingPage />} />
              <Route path="/share/:token" element={<SharedFilePage />} />
              <Route
                path="/dashboard/*"
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/*"
                element={
                  <ProtectedRoute requiredRoles={['admin']}>
                    <AdminDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/files/*"
                element={
                  <ProtectedRoute>
                    <FileView />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/security/mfa-setup"
                element={
                  <ProtectedRoute>
                    <MFASetup />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </div>
        </KeycloakProvider>
      </Router>
    </Provider>
  );
}

export default App;