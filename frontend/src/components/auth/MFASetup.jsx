// src/components/auth/MFASetup.jsx
import React, { useState, useEffect } from 'react';
import { useKeycloak } from '@react-keycloak/web';
import { checkMFAStatus } from '../../services/authService';
import { QrCode, Shield, Key, CheckCircle, XCircle } from 'lucide-react';

const MFASetup = () => {
    const { keycloak } = useKeycloak();
    const [mfaEnabled, setMfaEnabled] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        checkMFAStatus();
    }, []);

    const checkMFAStatus = async () => {
        try {
            setLoading(true);
            const isEnabled = await checkMFAStatus(keycloak);
            setMfaEnabled(isEnabled);
        } catch (error) {
            setError('Failed to check MFA status');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleEnableMFA = async () => {
        try {
            // This will redirect to Keycloak's TOTP setup page
            await keycloak.login({
                action: 'configure-totp'
            });
        } catch (error) {
            setError('Failed to initiate MFA setup');
            console.error(error);
        }
    };

    const handleDisableMFA = async () => {
        try {
            // Implement MFA disable logic here
            // This would require a custom endpoint in your backend
            const response = await fetch('/api/auth/disable-mfa', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${keycloak.token}`
                }
            });

            if (response.ok) {
                setMfaEnabled(false);
            } else {
                throw new Error('Failed to disable MFA');
            }
        } catch (error) {
            setError('Failed to disable MFA');
            console.error(error);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-[400px]">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto p-6">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                <div className="p-6">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <Shield className="h-6 w-6 text-blue-600" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900">
                                Two-Factor Authentication
                            </h2>
                            <p className="text-gray-500">
                                Add an extra layer of security to your account
                            </p>
                        </div>
                    </div>

                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
                            <XCircle className="h-5 w-5" />
                            <span>{error}</span>
                        </div>
                    )}

                    <div className="bg-gray-50 rounded-lg p-6 mb-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <Key className="h-5 w-5 text-gray-500" />
                                <div>
                                    <h3 className="font-medium text-gray-900">
                                        2FA Status
                                    </h3>
                                    <p className="text-sm text-gray-500">
                                        {mfaEnabled ? 'Enabled and active' : 'Not configured'}
                                    </p>
                                </div>
                            </div>
                            <div className={`px-3 py-1 rounded-full text-sm font-medium ${mfaEnabled
                                ? 'bg-green-100 text-green-800'
                                : 'bg-yellow-100 text-yellow-800'
                                }`}>
                                {mfaEnabled ? 'Enabled' : 'Disabled'}
                            </div>
                        </div>
                    </div>

                    {mfaEnabled ? (
                        <div className="space-y-4">
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                <CheckCircle className="h-5 w-5 text-green-500" />
                                <span>Two-factor authentication is enabled</span>
                            </div>
                            <button
                                onClick={handleDisableMFA}
                                className="w-full px-4 py-2 border border-red-500 text-red-500 rounded-lg hover:bg-red-50 transition-colors"
                            >
                                Disable Two-Factor Authentication
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="p-4 border rounded-lg">
                                    <QrCode className="h-6 w-6 text-gray-500 mb-2" />
                                    <h4 className="font-medium text-gray-900 mb-1">
                                        Scan QR Code
                                    </h4>
                                    <p className="text-sm text-gray-500">
                                        Use an authenticator app to scan the QR code
                                    </p>
                                </div>
                                <div className="p-4 border rounded-lg">
                                    <Key className="h-6 w-6 text-gray-500 mb-2" />
                                    <h4 className="font-medium text-gray-900 mb-1">
                                        Enter Code
                                    </h4>
                                    <p className="text-sm text-gray-500">
                                        Enter the code from your authenticator app
                                    </p>
                                </div>
                            </div>

                            <button
                                onClick={handleEnableMFA}
                                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                Enable Two-Factor Authentication
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MFASetup;