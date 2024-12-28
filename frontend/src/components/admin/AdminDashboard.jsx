import React, { useState, useEffect } from 'react';
import { useKeycloak } from '@react-keycloak/web';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import {
    Users, HardDrive, Share2, FileText,
    Activity, Clock, X, UserPlus, Settings,
    AlertCircle, CheckCircle, XCircle
} from 'lucide-react';
import { checkAdminAccess, getSystemStats, getUserManagement, toggleUserStatus } from '../../services/adminApi';
import AddUserModal from './AddUserModal';
import api from '../../services/api';
import { formatStorageUsage, calculateStoragePercentage } from '../../utils/format';
const USER_STORAGE_LIMIT = 2147483648; // 2 GB


const Card = ({ children, className = '' }) => (
    <div className={`bg-white rounded-lg shadow-lg overflow-hidden ${className}`}>
        {children}
    </div>
);

const AdminDashboard = () => {
    const { keycloak } = useKeycloak();
    const [isAdmin, setIsAdmin] = useState(false);
    const [systemStats, setSystemStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activityData, setActivityData] = useState([]);
    const [addUserModalOpen, setAddUserModalOpen] = useState(false);

    useEffect(() => {
        if (keycloak.authenticated) {
            loadAdminData();
        }
    }, [keycloak.authenticated]);

    const handleAddUser = async (userData) => {
        try {
            const response = await api.post('/api/admin/create-user/', {
                first_name: userData.firstName,
                last_name: userData.lastName,
                email: userData.email,
                username: userData.username,
                password: userData.password,
                role: userData.role
            });
            // await loadAdminData(); // Refresh the user list
            console.log(response.data);
            return response.data;
        } catch (error) {
            console.error(error);
            throw new Error(error.response?.data?.message || 'Failed to create user');
        }
    };

    const loadAdminData = async () => {
        try {
            const accessResponse = await checkAdminAccess();
            setIsAdmin(accessResponse.is_admin);

            if (accessResponse.is_admin) {
                const [statsResponse, usersResponse] = await Promise.all([
                    getSystemStats(),
                    getUserManagement()
                ]);

                setSystemStats(statsResponse);
                setUsers(usersResponse);

                // Process activity data for chart
                const activityStats = statsResponse.daily_stats || [];
                setActivityData(activityStats.map(stat => ({
                    date: stat.date,
                    'Active Users': stat.active_users || statsResponse.active_users,
                    'New Users': stat.new_users
                })));
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to load admin data');
        } finally {
            setLoading(false);
        }
    };

    const handleToggleStatus = async (userId) => {
        try {
            await toggleUserStatus(userId);
            await loadAdminData(); // Refresh data
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to toggle user status');
        }
    };

    if (!keycloak.authenticated) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <AlertCircle className="h-16 w-16 text-yellow-500 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold">Please log in to access admin features</h2>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="flex justify-center items-center h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold text-red-600">Error: {error}</h2>
                </div>
            </div>
        );
    }

    if (!isAdmin) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <Settings className="h-16 w-16 text-gray-500 mx-auto mb-4" />
                    <h2 className="text-xl font-semibold">You do not have admin privileges</h2>
                </div>
            </div>
        );
    }

    const STORAGE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

    return (
        <div className="container mx-auto px-4 py-8 space-y-6">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-2xl font-bold text-gray-800">Admin Dashboard</h1>
                <button
                    className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    onClick={() => setAddUserModalOpen(true)}
                >
                    <UserPlus className="h-5 w-5" />
                    Add New User
                </button>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card>
                    <div className="p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Total Users</p>
                                <h3 className="text-2xl font-bold text-gray-900">{systemStats?.total_users || 0}</h3>
                            </div>
                            <div className="p-3 bg-blue-100 rounded-full">
                                <Users className="h-6 w-6 text-blue-600" />
                            </div>
                        </div>
                        <p className="text-sm text-gray-500">
                            {systemStats?.active_users || 0} active users
                        </p>
                    </div>
                </Card>

                <Card>
                    <div className="p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Total Files</p>
                                <h3 className="text-2xl font-bold text-gray-900">{systemStats?.total_files || 0}</h3>
                            </div>
                            <div className="p-3 bg-green-100 rounded-full">
                                <FileText className="h-6 w-6 text-green-600" />
                            </div>
                        </div>
                        <p className="text-sm text-gray-500">
                            {systemStats?.formatted_total_storage || '0 GB'} stored
                        </p>
                    </div>
                </Card>

                <Card>
                    <div className="p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <p className="text-sm font-medium text-gray-600">Active Shares</p>
                                <h3 className="text-2xl font-bold text-gray-900">{systemStats?.active_shares || 0}</h3>
                            </div>
                            <div className="p-3 bg-yellow-100 rounded-full">
                                <Share2 className="h-6 w-6 text-yellow-600" />
                            </div>
                        </div>
                        <p className="text-sm text-gray-500">
                            {systemStats?.total_shares || 0} total shares
                        </p>
                    </div>
                </Card>

                <Card>
                    <div className="p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <p className="text-sm font-medium text-gray-600">System Storage</p>
                                <h3 className="text-2xl font-bold text-gray-900">
                                    {systemStats?.storage_usage?.used_percentage.toFixed(1)}%
                                </h3>
                            </div>
                            <div className="p-3 bg-purple-100 rounded-full">
                                <HardDrive className="h-6 w-6 text-purple-600" />
                            </div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                                className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${systemStats?.storage_usage?.used_percentage || 0}%` }}
                            />
                        </div>
                        <p className="mt-2 text-sm text-gray-500">
                            {formatStorageUsage(
                                systemStats?.storage_usage?.used || 0,
                                systemStats?.storage_usage?.total || 0
                            )}
                        </p>
                    </div>
                </Card>
            </div>

            {/* Activity Chart */}
            <Card>
                <div className="p-6">
                    <h2 className="text-lg font-semibold mb-4">User Activity</h2>
                    <div className="h-[300px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={activityData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                <XAxis dataKey="date" />
                                <YAxis />
                                <Tooltip />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="Active Users"
                                    stroke="#3b82f6"
                                    strokeWidth={2}
                                    dot={false}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="New Users"
                                    stroke="#10b981"
                                    strokeWidth={2}
                                    dot={false}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </Card>

            {/* User Management */}
            <Card>
                <div className="p-6">
                    <h2 className="text-lg font-semibold mb-4">User Management</h2>
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead>
                                <tr>
                                    <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        User
                                    </th>
                                    <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Storage
                                    </th>
                                    <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Files
                                    </th>
                                    <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {users.map((user) => (
                                    <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="ml-4">
                                                    <div className="text-sm font-medium text-gray-900">
                                                        {user.username}
                                                    </div>
                                                    <div className="text-sm text-gray-500">
                                                        {user.email}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-900">
                                                {formatStorageUsage(
                                                    user.storage_used,
                                                    USER_STORAGE_LIMIT
                                                )}
                                            </div>
                                            <div className="w-full bg-gray-200 rounded-full h-1 mt-1">
                                                <div
                                                    className="bg-blue-600 h-1 rounded-full"
                                                    style={{
                                                        width: `${calculateStoragePercentage(user.storage_used, USER_STORAGE_LIMIT)}%`
                                                    }}
                                                />
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {user.file_count}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full
                                                ${user.is_active
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-red-100 text-red-800'}`}
                                            >
                                                {user.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <button
                                                onClick={() => setSelectedUser(user)}
                                                className="text-blue-600 hover:text-blue-900 mr-4"
                                            >
                                                Details
                                            </button>
                                            <button
                                                onClick={() => handleToggleStatus(user.id)}
                                                className="text-gray-600 hover:text-gray-900"
                                            >
                                                {user.is_active ? 'Disable' : 'Enable'}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </Card>

            {/* User Details Modal */}
            {selectedUser && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg max-w-2xl w-full p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold">User Details</h3>
                            <button
                                onClick={() => setSelectedUser(null)}
                                className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                            >
                                <X className="h-6 w-6 text-gray-500" />
                            </button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-4">
                                <h4 className="font-medium text-gray-500">Storage Usage</h4>
                                <div className="bg-gray-50 p-4 rounded-lg">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-gray-600">Used Space</span>
                                        <span className="font-medium">
                                            {selectedUser.formatted_storage} of {USER_STORAGE_LIMIT / 1024 / 1024 / 1024} GB
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                            style={{ width: `${selectedUser.formatted_storage / 2 * 100}%` }}
                                        />
                                    </div>
                                </div>
                            </div>
                            <div className="space-y-4">
                                <h4 className="font-medium text-gray-500">File Statistics</h4>
                                <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-600">Total Files</span>
                                        <span className="font-medium">{selectedUser.file_count}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-600">Active Shares</span>
                                        <span className="font-medium">{selectedUser.active_shares}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-600">Total Shares</span>
                                        <span className="font-medium">{selectedUser.total_shares}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="space-y-4">
                                <h4 className="font-medium text-gray-500">Recent Activity</h4>
                                <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                                    <div className="flex items-center gap-2">
                                        <Clock className="h-4 w-4 text-gray-500" />
                                        <span className="text-gray-600">Last Login:</span>
                                        <span className="font-medium">
                                            {selectedUser.last_login ? new Date(selectedUser.last_login).toLocaleString() : 'NA'}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Activity className="h-4 w-4 text-gray-500" />
                                        <span className="text-gray-600">Member Since:</span>
                                        <span className="font-medium">
                                            {new Date(selectedUser.date_joined).toLocaleString()}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div className="space-y-4">
                                <h4 className="font-medium text-gray-500">Account Settings</h4>
                                <div className="bg-gray-50 p-4 rounded-lg space-y-4">
                                    <div className="flex items-center justify-between">
                                        <span className="text-gray-600">Account Status</span>
                                        <span className={`px-2 py-1 rounded text-sm ${selectedUser.is_active
                                            ? 'bg-green-100 text-green-800'
                                            : 'bg-red-100 text-red-800'
                                            }`}>
                                            {selectedUser.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => {
                                            handleToggleStatus(selectedUser.id);
                                            setSelectedUser(null);
                                        }}
                                        className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                                    >
                                        {selectedUser.is_active ? 'Disable Account' : 'Enable Account'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Add User Modal */}
            <AddUserModal
                isOpen={addUserModalOpen}
                onClose={() => setAddUserModalOpen(false)}
                onAdd={handleAddUser}
            />

        </div>
    );
};

export default AdminDashboard;