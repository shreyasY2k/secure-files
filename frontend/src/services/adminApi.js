// src/services/adminApi.js
import api from './api';

export const checkAdminAccess = async () => {
    const response = await api.get('/api/admin/check-admin-access/');
    return response.data;
};

export const getSystemStats = async () => {
    const response = await api.get('/api/admin/system-stats/');
    return response.data;
};

export const getUserManagement = async () => {
    const response = await api.get('/api/admin/user-management/');
    return response.data;
};

export const getUserDetails = async (userId) => {
    const response = await api.get(`/api/admin/${userId}/details/`);
    return response.data;
};

export const toggleUserStatus = async (userId) => {
    const response = await api.post(`/api/admin/${userId}/toggle-status/`);
    return response.data;
};