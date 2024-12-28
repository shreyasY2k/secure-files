import React, { useState } from 'react';
import { useKeycloak } from '@react-keycloak/web';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
    LogOut, Shield, LayoutDashboard,
    Menu, X, ChevronDown, User, Settings,
    FileText, Upload
} from 'lucide-react';
import FileUploadModal from '../files/modals/FileUploadModal';

const FILE_UPLOAD_SUCCESS_EVENT = 'fileUploadSuccess';

const Navbar = () => {
    const { keycloak } = useKeycloak();
    const navigate = useNavigate();
    const location = useLocation();
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

    const isCurrentPath = (path) => {
        return location.pathname === path;
    };

    const handleLogin = () => {
        keycloak.login();
    };

    const handleLogout = () => {
        keycloak.logout();
        navigate('/');
    };

    const handleUploadComplete = () => {
        setIsUploadModalOpen(false);
        // Dispatch custom event for Dashboard to listen to
        window.dispatchEvent(new Event(FILE_UPLOAD_SUCCESS_EVENT));
    };

    const fetchDashboardData = async () => {
        try {
            const [storageResponse, filesResponse, sharedResponse] = await Promise.all([
                api.get('/api/files/storage-stats/'),
                api.get('/api/files/'),
                api.get('/api/files/shared-with-me/')
            ]);

            setStorageStats(storageResponse.data);
            setRecentFiles(filesResponse.data.slice(0, 5));
            setSharedFiles(sharedResponse.data);
            setError(null);
        } catch (err) {
            setError('Failed to load dashboard data');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const NavLink = ({ to, children, onClick }) => {
        const isActive = isCurrentPath(to);
        return (
            <Link
                to={to}
                onClick={onClick}
                className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-2 
                    ${isActive
                        ? 'bg-white/10 text-white'
                        : 'text-gray-100 hover:bg-white/10'}`}
            >
                {children}
            </Link>
        );
    };

    const UploadButton = () => (
        <button
            onClick={() => setIsUploadModalOpen(true)}
            className="px-3 py-2 rounded-lg transition-colors flex items-center gap-2 
                     text-gray-100 hover:bg-white/10"
        >
            <Upload className="h-4 w-4" />
            Upload File
        </button>
    );

    return (
        <>
            <nav className="bg-gradient-to-r from-blue-600 to-blue-700 shadow-lg">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16">
                        {/* Logo & Brand */}
                        <div className="flex items-center">
                            <Link to="/" className="flex items-center gap-2">
                                <Shield className="h-8 w-8 text-white" />
                                <span className="text-xl font-bold text-white">SecureShare</span>
                            </Link>
                        </div>

                        {/* Desktop Navigation */}
                        <div className="hidden md:flex items-center gap-2">
                            {keycloak.authenticated && (
                                <>
                                    <UploadButton />

                                    <NavLink to="/dashboard">
                                        <LayoutDashboard className="h-4 w-4" />
                                        Dashboard
                                    </NavLink>

                                    <NavLink to="/files">
                                        <FileText className="h-4 w-4" />
                                        My Files
                                    </NavLink>


                                    {keycloak.hasRealmRole('admin') && (
                                        <NavLink to="/admin">
                                            <Settings className="h-4 w-4" />
                                            Admin
                                        </NavLink>
                                    )}

                                    {/* Profile Dropdown */}
                                    <div className="relative ml-3">
                                        <button
                                            onClick={() => setIsProfileOpen(!isProfileOpen)}
                                            className="flex items-center gap-2 px-3 py-2 rounded-lg text-white hover:bg-white/10 transition-colors"
                                        >
                                            <div className="h-8 w-8 rounded-full bg-white/20 flex items-center justify-center">
                                                <User className="h-5 w-5 text-white" />
                                            </div>
                                            <ChevronDown className="h-4 w-4" />
                                        </button>

                                        {isProfileOpen && (
                                            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-50 animate-fadeIn">
                                                <div className="px-4 py-2 border-b">
                                                    <p className="text-sm font-medium text-gray-900">
                                                        {keycloak.tokenParsed?.preferred_username}
                                                    </p>
                                                    <p className="text-sm text-gray-500">
                                                        {keycloak.tokenParsed?.email}
                                                    </p>
                                                </div>
                                                <button
                                                    onClick={handleLogout}
                                                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                                                >
                                                    <LogOut className="h-4 w-4" />
                                                    Sign out
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </>
                            )}

                            {!keycloak.authenticated && (
                                <button
                                    onClick={handleLogin}
                                    className="bg-white text-blue-600 px-6 py-2 rounded-lg font-medium 
                                             hover:bg-blue-50 transition-colors flex items-center gap-2"
                                >
                                    <User className="h-4 w-4" />
                                    Sign In
                                </button>
                            )}
                        </div>

                        {/* Mobile Menu Button */}
                        <div className="flex items-center md:hidden">
                            <button
                                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                                className="text-white p-2 rounded-lg hover:bg-white/10 transition-colors"
                            >
                                {isMobileMenuOpen ? (
                                    <X className="h-6 w-6" />
                                ) : (
                                    <Menu className="h-6 w-6" />
                                )}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Mobile Menu */}
                {isMobileMenuOpen && (
                    <div className="md:hidden bg-blue-700 border-t border-white/10 animate-slideDown">
                        <div className="px-2 pt-2 pb-3 space-y-1">
                            {keycloak.authenticated ? (
                                <>
                                    <UploadButton />
                                    <NavLink
                                        to="/dashboard"
                                        onClick={() => setIsMobileMenuOpen(false)}
                                    >
                                        <LayoutDashboard className="h-4 w-4" />
                                        Dashboard
                                    </NavLink>

                                    <NavLink
                                        to="/files"
                                        onClick={() => setIsMobileMenuOpen(false)}
                                    >
                                        <FileText className="h-4 w-4" />
                                        My Files
                                    </NavLink>


                                    {keycloak.hasRealmRole('admin') && (
                                        <NavLink
                                            to="/admin"
                                            onClick={() => setIsMobileMenuOpen(false)}
                                        >
                                            <Settings className="h-4 w-4" />
                                            Admin
                                        </NavLink>
                                    )}

                                    <button
                                        onClick={handleLogout}
                                        className="w-full px-3 py-2 text-left text-white hover:bg-white/10 
                                                 rounded-lg transition-colors flex items-center gap-2"
                                    >
                                        <LogOut className="h-4 w-4" />
                                        Sign out
                                    </button>
                                </>
                            ) : (
                                <button
                                    onClick={handleLogin}
                                    className="w-full px-3 py-2 text-white hover:bg-white/10 
                                             rounded-lg transition-colors flex items-center gap-2"
                                >
                                    <User className="h-4 w-4" />
                                    Sign In
                                </button>
                            )}
                        </div>
                    </div>
                )}
            </nav>

            {/* File Upload Modal */}
            {isUploadModalOpen && (
                <FileUploadModal
                    isOpen={isUploadModalOpen}
                    onClose={() => setIsUploadModalOpen(false)}
                    onUploadComplete={handleUploadComplete}
                />
            )}
        </>
    );
};

export default Navbar;