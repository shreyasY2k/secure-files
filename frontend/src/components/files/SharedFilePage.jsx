import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../../services/api';

const GuestView = () => {
    const { token } = useParams();
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [password, setPassword] = useState('');
    const [isPasswordVerified, setIsPasswordVerified] = useState(false);
    const [downloading, setDownloading] = useState(false);
    const [accessToken, setAccessToken] = useState(null);

    useEffect(() => {
        fetchFileInfo();
    }, [token]);

    const fetchFileInfo = async () => {
        try {
            setLoading(true);
            const response = await api.get(`/api/files/shared/${token}/`);
            setFile(response.data);
            setError(null);

            // Check if we have a stored access token
            const storedToken = localStorage.getItem(`file_access_token_${token}`);
            if (storedToken) {
                setAccessToken(storedToken);
                setIsPasswordVerified(true);
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to load file information');
        } finally {
            setLoading(false);
        }
    };

    const handlePasswordSubmit = async (e) => {
        e.preventDefault();
        try {
            setLoading(true);
            const response = await api.post(`/api/sharelinks/${token}/verify-password/`, {
                password
            });

            if (response.data.access_token) {
                const newAccessToken = response.data.access_token;
                setAccessToken(newAccessToken);
                setIsPasswordVerified(true);
                localStorage.setItem(`file_access_token_${token}`, newAccessToken);
            }

            setError(null);
        } catch (err) {
            console.error('Password verification error:', err);
            setError('Invalid password');
            setPassword('');
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async () => {
        try {
            setDownloading(true);
            const headers = {};

            if (file.is_password_protected && accessToken) {
                headers['Authorization'] = `Bearer ${accessToken}`;
            }

            const response = await api.get(`/api/files/download/${token}/`, {
                responseType: 'blob',
                headers
            });


            const fileData = response.data;

            // Create download link
            const url = window.URL.createObjectURL(fileData);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', file.name);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            window.URL.revokeObjectURL(url);

        } catch (err) {
            console.error('Download error:', err);
            if (err.response?.status === 401) {
                localStorage.removeItem(`file_access_token_${token}`);
                setIsPasswordVerified(false);
                setAccessToken(null);
                setError('Access token expired. Please enter the password again.');
            } else {
                setError('Failed to download file');
            }
        } finally {
            setDownloading(false);
            fetchFileInfo();
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100">
                <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
                    <div className="text-center text-red-500 mb-4">
                        <div className="text-4xl mb-2">⚠️</div>
                        <h2 className="text-xl font-semibold">Error</h2>
                        <p>{error}</p>
                    </div>
                </div>
            </div>
        );
    }

    if (file?.is_password_protected && !isPasswordVerified) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
                <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
                    <div className="text-center mb-6">
                        <div className="text-4xl mb-2">🔒</div>
                        <h2 className="text-2xl font-bold">Protected File</h2>
                        <p className="text-gray-600 mt-2">This file is password protected</p>
                    </div>

                    <form onSubmit={handlePasswordSubmit} className="space-y-4">
                        <div>
                            <label className="block text-gray-700 text-sm font-bold mb-2">
                                Password
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="Enter password"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={!password || loading}
                            className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Verifying...' : 'Access File'}
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
            <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
                <div className="text-center mb-6">
                    <div className="text-4xl mb-2">📄</div>
                    <h2 className="text-2xl font-bold">{file.name}</h2>
                </div>

                <div className="space-y-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <p className="text-sm text-gray-500">Size</p>
                                <p className="font-medium">{file.formatted_size}</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">Uploaded</p>
                                <p className="font-medium">
                                    {new Date(file.uploaded_at).toLocaleDateString()}
                                </p>
                            </div>
                        </div>
                    </div>

                    {file.max_access_count && (
                        <div className="bg-blue-50 p-4 rounded-lg">
                            <p className="text-sm text-blue-600">
                                Downloads: {file.access_count} / {file.max_access_count}
                            </p>
                        </div>
                    )}

                    <div className="bg-yellow-50 p-4 rounded-lg">
                        <p className="text-sm text-yellow-600">
                            Expires on: {new Date(file.expires_at).toLocaleString()}
                        </p>
                    </div>

                    <button
                        onClick={handleDownload}
                        disabled={downloading}
                        className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 disabled:bg-gray-300 flex items-center justify-center gap-2"
                    >
                        {downloading ? (
                            <>
                                <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
                                Downloading...
                            </>
                        ) : (
                            <>
                                <span>⬇️</span>
                                Download File
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default GuestView;