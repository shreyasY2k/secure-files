// src/services/api.js
import axios from 'axios';
import keycloak from './keycloak';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
});

// Request interceptor for API calls
api.interceptors.request.use(
    async (config) => {
        if (keycloak.authenticated) {
            const token = keycloak.token;
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for API calls
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            try {
                await keycloak.updateToken(5);
                originalRequest.headers.Authorization = `Bearer ${keycloak.token}`;
                return api(originalRequest);
            } catch (refreshError) {
                await keycloak.logout();
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

// File operations
export const uploadFile = async (file, fileName, mimeType, onProgress) => {
    const formData = new FormData();
    formData.append('file', file, fileName);
    formData.append('original_filename', fileName);
    formData.append('mime_type', mimeType);
    console.log('MimeType:', mimeType);

    const response = await api.post('/api/files/upload/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
            if (onProgress) {
                const percentCompleted = Math.round(
                    (progressEvent.loaded * 100) / progressEvent.total
                );
                onProgress(percentCompleted);
            }
        },
    });

    return response.data;
};

export const getFiles = async () => {
    const response = await api.get('/api/files/');
    return response.data;
};

export const getFileStatistics = async (fileId) => {
    const response = await api.get(`/api/files/${fileId}/statistics/`);
    return response.data;
};

export const getUserStorageStats = async () => {
    const response = await api.get('/api/files/storage-stats/');
    return response.data;
};

// Share operations
export const shareFile = async (fileId, userId, permission = 'view') => {
    try {
        const response = await api.post(`/api/files/${fileId}/share/`, {
            shared_with: userId,  // Match the backend parameter
            permission: permission,
        });
        return response.data;
    } catch (error) {
        if (error.response) {
            throw new Error(error.response.data.error || 'Failed to share file');
        }
        throw error;
    }
};

export const generateShareLink = async (fileId, options = {}) => {
    const response = await api.post(`/api/files/${fileId}/share-link/`, {
        expires_in_hours: options.expiresInHours || 24,
        max_access_count: options.maxAccessCount,
        password: options.password,
    });
    return response.data;
};

export const verifyShareLinkPassword = async (token, password) => {
    const response = await api.post(`/api/sharelinks/${token}/verify-password/`, {
        password,
    });
    return response.data;
};

// Access shared content
export const getSharedFileInfo = async (token) => {
    const response = await api.get(`/api/files/shared/${token}/`);
    return response.data;
};

export const downloadSharedFile = async (token, accessToken = null) => {
    const headers = {};
    if (accessToken) {
        headers.Authorization = `Bearer ${accessToken}`;
    }

    const response = await api.get(`/api/files/download/${token}/`, {
        responseType: 'blob',
        headers,
    });
    return response.data;
};

// File management
export const deleteFile = async (fileId) => {
    await api.delete(`/api/files/${fileId}/`);
};

export const getSharedWithMe = async () => {
    const response = await api.get('/api/files/shared-with-me/');
    return response.data;
};

export const revokeAccess = async (fileId, userId) => {
    await api.delete(`/api/files/${fileId}/share/${userId}/`);
};

export const getFileAccessHistory = async (fileId) => {
    const response = await api.get(`/api/files/${fileId}/access-history/`);
    return response.data;
};

export default api;