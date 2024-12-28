import React, { useState } from 'react';
import { shareFile, generateShareLink } from '../../../services/api';
import {
    X, Link, Copy, Clock, Shield, Lock,
    User, CheckCircle, Share2, Eye, Download,
    AlertCircle
} from 'lucide-react';

const ShareFileModal = ({ file, onClose, onShare }) => {
    const [activeTab, setActiveTab] = useState('user'); // 'user' or 'link'
    const [userId, setUserId] = useState('');
    const [permissions, setPermissions] = useState('view');
    const [expirationHours, setExpirationHours] = useState(24);
    const [maxAccess, setMaxAccess] = useState('');
    const [password, setPassword] = useState('');
    const [shareLink, setShareLink] = useState('');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);
    const [copied, setCopied] = useState(false);

    const handleShareWithUser = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            await shareFile(file.id, userId, permissions);
            onShare?.();
            setUserId('');
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to share file');
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateLink = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await generateShareLink(file.id, {
                expiresInHours: parseInt(expirationHours),
                maxAccessCount: maxAccess ? parseInt(maxAccess) : null,
                password: password || null
            });

            const shareUrl = `${window.location.origin}/share/${response.token}`;
            setShareLink(shareUrl);
            setCopied(false);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to generate share link');
        } finally {
            setLoading(false);
        }
    };

    const copyToClipboard = async () => {
        try {
            await navigator.clipboard.writeText(shareLink);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            setError('Failed to copy to clipboard');
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
                {/* Header */}
                <div className="p-4 border-b flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-semibold text-gray-800">Share File</h2>
                        <p className="text-sm text-gray-500 mt-1">{file.name}</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                    >
                        <X className="h-5 w-5 text-gray-500" />
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b">
                    <button
                        className={`flex-1 p-4 text-sm font-medium ${activeTab === 'user'
                            ? 'text-blue-600 border-b-2 border-blue-600'
                            : 'text-gray-500 hover:text-gray-700'
                            }`}
                        onClick={() => setActiveTab('user')}
                    >
                        <div className="flex items-center justify-center gap-2">
                            <User className="h-4 w-4" />
                            Share with User
                        </div>
                    </button>
                    <button
                        className={`flex-1 p-4 text-sm font-medium ${activeTab === 'link'
                            ? 'text-blue-600 border-b-2 border-blue-600'
                            : 'text-gray-500 hover:text-gray-700'
                            }`}
                        onClick={() => setActiveTab('link')}
                    >
                        <div className="flex items-center justify-center gap-2">
                            <Link className="h-4 w-4" />
                            Generate Link
                        </div>
                    </button>
                </div>

                <div className="p-6">
                    {activeTab === 'user' ? (
                        /* Share with User Form */
                        <form onSubmit={handleShareWithUser} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    User Email
                                </label>
                                <input
                                    type="email"
                                    value={userId}
                                    onChange={(e) => setUserId(e.target.value)}
                                    placeholder="Enter user's email"
                                    className="w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    required
                                />
                            </div>

                            {/* <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Permissions
                                </label>
                                <div className="grid grid-cols-2 gap-3">
                                    <button
                                        type="button"
                                        onClick={() => setPermissions('view')}
                                        className={`p-3 flex items-center justify-center gap-2 rounded-lg border ${permissions === 'view'
                                            ? 'bg-blue-50 border-blue-500 text-blue-700'
                                            : 'hover:bg-gray-50'
                                            }`}
                                    >
                                        <Eye className="h-4 w-4" />
                                        View Only
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setPermissions('download')}
                                        className={`p-3 flex items-center justify-center gap-2 rounded-lg border ${permissions === 'download'
                                            ? 'bg-blue-50 border-blue-500 text-blue-700'
                                            : 'hover:bg-gray-50'
                                            }`}
                                    >
                                        <Download className="h-4 w-4" />
                                        Download
                                    </button>
                                </div>
                            </div> */}

                            {error && (
                                <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
                                    <AlertCircle className="h-4 w-4" />
                                    <span className="text-sm">{error}</span>
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading || !userId}
                                className="w-full py-2.5 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                                         disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                                        Sharing...
                                    </>
                                ) : (
                                    <>
                                        <Share2 className="h-4 w-4" />
                                        Share with User
                                    </>
                                )}
                            </button>
                        </form>
                    ) : (
                        /* Generate Link Form */
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    <div className="flex items-center gap-2">
                                        <Clock className="h-4 w-4" />
                                        Link Expiration
                                    </div>
                                </label>
                                <select
                                    value={expirationHours}
                                    onChange={(e) => setExpirationHours(e.target.value)}
                                    className="w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="24">24 hours</option>
                                    <option value="48">48 hours</option>
                                    <option value="72">72 hours</option>
                                    <option value="168">1 week</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    <div className="flex items-center gap-2">
                                        <Shield className="h-4 w-4" />
                                        Access Limit (Optional)
                                    </div>
                                </label>
                                <input
                                    type="number"
                                    value={maxAccess}
                                    onChange={(e) => setMaxAccess(e.target.value)}
                                    placeholder="Leave blank for unlimited"
                                    min="1"
                                    className="w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    <div className="flex items-center gap-2">
                                        <Lock className="h-4 w-4" />
                                        Password Protection (Optional)
                                    </div>
                                </label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Leave blank for no password"
                                    className="w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                />
                            </div>

                            {error && (
                                <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
                                    <AlertCircle className="h-4 w-4" />
                                    <span className="text-sm">{error}</span>
                                </div>
                            )}

                            {!shareLink ? (
                                <button
                                    onClick={handleGenerateLink}
                                    disabled={loading}
                                    className="w-full py-2.5 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 
                                             disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                >
                                    {loading ? (
                                        <>
                                            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                                            Generating...
                                        </>
                                    ) : (
                                        <>
                                            <Link className="h-4 w-4" />
                                            Generate Link
                                        </>
                                    )}
                                </button>
                            ) : (
                                <div className="space-y-3">
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="text"
                                            value={shareLink}
                                            readOnly
                                            className="flex-1 p-2.5 bg-gray-50 border rounded-lg"
                                        />
                                        <button
                                            onClick={copyToClipboard}
                                            className="p-2.5 text-gray-600 hover:text-blue-600 border rounded-lg 
                                                     hover:border-blue-600 transition-colors"
                                        >
                                            {copied ? (
                                                <CheckCircle className="h-5 w-5 text-green-600" />
                                            ) : (
                                                <Copy className="h-5 w-5" />
                                            )}
                                        </button>
                                    </div>

                                    <div className="bg-gray-50 p-3 rounded-lg space-y-2">
                                        {password && (
                                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                                <Lock className="h-4 w-4" />
                                                Password protected
                                            </div>
                                        )}
                                        {maxAccess && (
                                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                                <Shield className="h-4 w-4" />
                                                Limited to {maxAccess} accesses
                                            </div>
                                        )}
                                        <div className="flex items-center gap-2 text-sm text-gray-600">
                                            <Clock className="h-4 w-4" />
                                            Expires in {expirationHours} hours
                                        </div>
                                    </div>

                                    <button
                                        onClick={() => setShareLink('')}
                                        className="w-full py-2.5 px-4 bg-gray-100 text-gray-700 rounded-lg 
                                                 hover:bg-gray-200 transition-colors"
                                    >
                                        Generate New Link
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ShareFileModal;