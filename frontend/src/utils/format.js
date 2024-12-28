// utils/format.js

export const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';

    const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    // Handle numbers too large for the available units
    if (i >= units.length) {
        return 'Size too large';
    }

    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${units[i]}`;
};

export const formatStorageUsage = (used, total) => {
    const usedFormatted = formatFileSize(used);
    const totalFormatted = formatFileSize(total);

    return `${usedFormatted} of ${totalFormatted}`;
};

// Each user has 2GB allocation
export const USER_STORAGE_LIMIT = 2 * 1024 * 1024 * 1024; // 2GB in bytes

export const calculateStoragePercentage = (used, total) => {
    if (!total || total === 0) return 0;
    return Math.min(100, (used / total) * 100);
};