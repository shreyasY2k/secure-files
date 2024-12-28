import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Upload, FileText, BarChart2, HardDrive, Share2, Download, Clock } from 'lucide-react';
import api from '../../services/api';
import FileView from '../files/FileView';
import { formatStorageUsage } from '../../utils/format';
const FILE_UPLOAD_SUCCESS_EVENT = 'fileUploadSuccess';

// Custom Card Components
const Card = ({ children, className = '' }) => (
    <div className={`bg-white rounded-lg shadow-lg overflow-hidden ${className}`}>
        {children}
    </div>
);

const CardHeader = ({ children, className = '' }) => (
    <div className={`p-4 border-b border-gray-200 ${className}`}>
        {children}
    </div>
);

const CardContent = ({ children, className = '' }) => (
    <div className={`p-4 ${className}`}>
        {children}
    </div>
);

const CardTitle = ({ children, className = '' }) => (
    <h3 className={`text-lg font-semibold text-gray-900 ${className}`}>
        {children}
    </h3>
);

const Dashboard = () => {
    const [storageStats, setStorageStats] = useState(null);
    const [recentFiles, setRecentFiles] = useState([]);
    const [sharedFiles, setSharedFiles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchDashboardData();

        // Add event listener for file upload success
        window.addEventListener(FILE_UPLOAD_SUCCESS_EVENT, fetchDashboardData);

        // Cleanup
        return () => {
            window.removeEventListener(FILE_UPLOAD_SUCCESS_EVENT, fetchDashboardData);
        };
    }, []);


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

    const handleFileUpload = () => {
        setShowUploadModal(true);
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    const STORAGE_COLORS = ['#3b82f6', '#e5e7eb'];
    const storageData = [
        { name: 'Used', value: storageStats?.used_storage || 0 },
        { name: 'Free', value: (storageStats?.total_storage || 0) - (storageStats?.used_storage || 0) }
    ];

    return (
        <div className="container mx-auto px-4 py-8 space-y-6">
            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* <button
                    onClick={handleFileUpload}
                    className="flex items-center justify-center gap-2 p-4 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-all shadow-lg hover:shadow-xl"
                >
                    <Upload className="h-5 w-5" />
                    <span className="font-semibold">Upload File</span>
                </button> */}
                <button className="flex items-center justify-center gap-2 p-4 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-all shadow-lg hover:shadow-xl">
                    <Clock className="h-5 w-5" />
                    <span className="font-semibold">Recent Files</span>
                </button>
                <button className="flex items-center justify-center gap-2 p-4 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-all shadow-lg hover:shadow-xl">
                    <BarChart2 className="h-5 w-5" />
                    <span className="font-semibold">View Statistics</span>
                </button>
                <input
                    type="file"
                    id="fileUpload"
                    className="hidden"
                    onChange={(e) => handleFileUpload(e.target.files[0])}
                />
            </div>

            {/* Storage Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Storage Usage</CardTitle>
                        <HardDrive className="h-5 w-5 text-gray-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-gray-600">Used Space</span>
                            <span className="font-medium">
                                {formatStorageUsage(storageStats?.used_storage, storageStats?.total_storage)}
                            </span>
                        </div>
                        <div className="space-y-4">
                            <div className="h-2.5 w-full bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-blue-600 transition-all duration-500 ease-in-out"
                                    style={{ width: `${storageStats?.storage_percentage}%` }}
                                />
                            </div>
                            <div className="h-[150px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={storageData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={40}
                                            outerRadius={60}
                                            paddingAngle={2}
                                            dataKey="value"
                                        >
                                            {storageData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={STORAGE_COLORS[index]} />
                                            ))}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Share Links</CardTitle>
                        <Share2 className="h-5 w-5 text-gray-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="flex justify-between items-center">
                            <div>
                                <p className="text-3xl font-bold text-blue-600">{storageStats?.used_links}</p>
                                <p className="text-gray-500">Active share links</p>
                            </div>
                            <div className="text-right">
                                <p className="text-lg font-semibold text-green-500">
                                    {storageStats?.max_links - storageStats?.used_links}
                                </p>
                                <p className="text-gray-500">Links remaining</p>
                            </div>
                        </div>
                        <div className="mt-4">
                            <div className="h-2.5 w-full bg-gray-200 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-green-500 transition-all duration-500 ease-in-out"
                                    style={{ width: `${(storageStats?.used_links / storageStats?.max_links) * 100}%` }}
                                />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Recent Files & Shared Files */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Recent Files</CardTitle>
                        <FileText className="h-5 w-5 text-gray-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="divide-y">
                            <FileView
                                files={recentFiles}
                                onRefresh={fetchDashboardData}
                                showControls={false}
                                className="bg-white rounded-lg shadow overflow-hidden"
                            />
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle>Shared With Me</CardTitle>
                        <Share2 className="h-5 w-5 text-gray-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="divide-y">
                            {sharedFiles.map(file => (
                                <div key={file.id} className="py-3 flex justify-between items-center group">
                                    <div>
                                        <p className="font-medium text-gray-900">{file.name}</p>
                                        <p className="text-sm text-gray-500">
                                            Shared by {file.owner_name} • {new Date(file.uploaded_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <button className="p-2 text-blue-600 hover:bg-blue-50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
                                        <Download className="h-4 w-4" />
                                    </button>
                                </div>
                            ))}
                            {sharedFiles.length === 0 && (
                                <div className="py-8 text-center text-gray-500">
                                    No files have been shared with you yet
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default Dashboard;