import React, { useState, useEffect, useCallback } from 'react';
import {
    Search, Filter, SortAsc, SortDesc, Grid, List, ChevronDown
} from 'lucide-react';
import api from '../../services/api';
import FilePreviewModal from './modals/FilePreviewModal';
import ShareFileModal from './modals/ShareFileModal';
import FileListView from './FileListView';
import { useKeycloak } from '@react-keycloak/web';
import debounce from 'lodash/debounce';

const FILE_UPLOAD_SUCCESS_EVENT = 'file_upload_success';

const QuickFilter = ({ active, onClick, children }) => (
    <button
        onClick={onClick}
        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${active ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
            }`}
    >
        {children}
    </button>
);

const FileView = ({
    files: externalFiles,
    onRefresh,
    showControls = true, // New prop to control UI sections
    className = "max-w-7xl mx-auto px-4 py-8" // Make className configurable
}) => {
    const { keycloak } = useKeycloak();
    const isAdmin = keycloak.hasRealmRole('admin');

    // State management
    const [files, setFiles] = useState(externalFiles || []);
    const [loading, setLoading] = useState(!externalFiles);
    const [error, setError] = useState(null);
    const [viewMode, setViewMode] = useState('list');
    const [sortField, setSortField] = useState('uploaded_at');
    const [sortOrder, setSortOrder] = useState('desc');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const [showPreview, setShowPreview] = useState(false);
    const [showShare, setShowShare] = useState(false);
    const [showFilterMenu, setShowFilterMenu] = useState(false);
    const [activeView, setActiveView] = useState('all');

    // Filter states
    const [filters, setFilters] = useState({
        type: 'all',
        dateRange: 'all',
        sharedFilter: 'all'
    });

    // File handling functions
    const handlePreview = (file) => {
        setSelectedFile(file);
        setShowPreview(true);
    };

    const handleShare = (file) => {
        setSelectedFile(file);
        setShowShare(true);
    };

    const handleDownload = async (file) => {
        try {
            const response = await api.get(`/api/files/${file.id}/content/?download=true`, {
                responseType: 'blob'
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', file.name);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Download error:', err);
            setError('Failed to download file');
        }
    };

    const handleDelete = async (file) => {
        try {
            await api.delete(`/api/files/${file.id}/`);
            if (onRefresh) {
                onRefresh();
            } else {
                fetchFiles();
            }
        } catch (err) {
            console.error('Delete error:', err);
            setError('Failed to delete file');
        }
    };

    // Only fetch if no external files provided
    const fetchFiles = useCallback(async (searchTerm = searchQuery) => {
        if (externalFiles) return;

        try {
            setLoading(true);
            const endpoint = activeView === 'shared' ? '/api/files/shared-with-me/' : '/api/files/';

            const params = showControls ? {
                sort_by: sortField,
                order: sortOrder,
                search: searchTerm,
                file_type: filters.type !== 'all' ? filters.type : undefined,
                date_range: filters.dateRange !== 'all' ? filters.dateRange : undefined,
            } : {};

            const response = await api.get(endpoint, { params });
            setFiles(response.data);
            setError(null);
        } catch (err) {
            setError('Failed to load files');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [activeView, sortField, sortOrder, filters, searchQuery, externalFiles, showControls]);

    // Update local files when external files change
    useEffect(() => {
        if (externalFiles) {
            setFiles(externalFiles);
            setLoading(false);
        }
    }, [externalFiles]);

    // Only fetch if no external files
    useEffect(() => {
        if (!externalFiles) {
            fetchFiles();
        }
    }, [activeView, sortField, sortOrder, filters, externalFiles]);

    // Event handlers
    const handleSearch = (e) => {
        const query = e.target.value;
        setSearchQuery(query);
        debouncedSearch(query);
    };

    const handleSort = (field) => {
        if (sortField === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortOrder('desc');
        }
    };

    const handleViewChange = (view) => {
        setActiveView(view);
        setFiles([]);
        setLoading(true);
    };

    const handleFilterChange = (filterType, value) => {
        setFilters(prev => ({
            ...prev,
            [filterType]: value
        }));
    };

    // Debounced search
    const debouncedSearch = useCallback(
        debounce((query) => {
            fetchFiles(query);
        }, 300),
        [fetchFiles]
    );

    useEffect(() => {
        const handleFileUploadSuccess = () => {
            console.log('File upload success detected, refreshing list...');
            fetchFiles();
        };

        window.addEventListener(FILE_UPLOAD_SUCCESS_EVENT, handleFileUploadSuccess);
        return () => {
            window.removeEventListener(FILE_UPLOAD_SUCCESS_EVENT, handleFileUploadSuccess);
        };
    }, [fetchFiles]);

    return (
        <div className={className}>
            {showControls && (
                <>
                    {/* View Selection */}
                    <div className="mb-8">
                        <div className="flex items-center gap-4">
                            <QuickFilter
                                active={activeView === 'all'}
                                onClick={() => handleViewChange('all')}
                            >
                                All Files
                            </QuickFilter>
                            <QuickFilter
                                active={activeView === 'shared'}
                                onClick={() => handleViewChange('shared')}
                            >
                                Shared With Me
                            </QuickFilter>
                        </div>
                    </div>

                    {/* Search and Filters */}
                    <div className="bg-white rounded-lg shadow mb-6">
                        <div className="p-4 flex flex-wrap items-center justify-between gap-4">
                            {/* Search */}
                            <div className="flex-1 min-w-[200px] max-w-md">
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                                    <input
                                        type="text"
                                        placeholder="Search files..."
                                        value={searchQuery}
                                        onChange={handleSearch}
                                        className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>

                            <div className="flex items-center gap-4">
                                {/* Filters */}
                                <div className="relative">
                                    <button
                                        onClick={() => setShowFilterMenu(!showFilterMenu)}
                                        className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-gray-50"
                                    >
                                        <Filter className="h-4 w-4" />
                                        Filters
                                        <ChevronDown className="h-4 w-4" />
                                    </button>

                                    {showFilterMenu && (
                                        <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg z-10 p-4">
                                            <div className="space-y-4">
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        File Type
                                                    </label>
                                                    <select
                                                        value={filters.type}
                                                        onChange={(e) => handleFilterChange('type', e.target.value)}
                                                        className="w-full p-2 border rounded-lg"
                                                    >
                                                        <option value="all">All Types</option>
                                                        <option value="document">Documents</option>
                                                        <option value="image">Images</option>
                                                        <option value="other">Others</option>
                                                    </select>
                                                </div>

                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        Date Range
                                                    </label>
                                                    <select
                                                        value={filters.dateRange}
                                                        onChange={(e) => handleFilterChange('dateRange', e.target.value)}
                                                        className="w-full p-2 border rounded-lg"
                                                    >
                                                        <option value="all">All Time</option>
                                                        <option value="7days">Last 7 Days</option>
                                                        <option value="30days">Last 30 Days</option>
                                                        <option value="90days">Last 90 Days</option>
                                                    </select>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* View Mode Toggle */}
                                <div className="flex items-center gap-1 border rounded-lg p-1">
                                    <button
                                        onClick={() => setViewMode('list')}
                                        className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-50 text-blue-600' : 'text-gray-500 hover:bg-gray-50'}`}
                                    >
                                        <List className="h-4 w-4" />
                                    </button>
                                    <button
                                        onClick={() => setViewMode('grid')}
                                        className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-50 text-blue-600' : 'text-gray-500 hover:bg-gray-50'}`}
                                    >
                                        <Grid className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Sort Controls */}
                        {viewMode === 'list' && (
                            <div className="px-4 py-2 border-t flex gap-4">
                                <button
                                    onClick={() => handleSort('name')}
                                    className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
                                >
                                    Name
                                    {sortField === 'name' && (
                                        sortOrder === 'asc' ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />
                                    )}
                                </button>
                                <button
                                    onClick={() => handleSort('uploaded_at')}
                                    className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
                                >
                                    Date
                                    {sortField === 'uploaded_at' && (
                                        sortOrder === 'asc' ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />
                                    )}
                                </button>
                            </div>
                        )}
                    </div>
                </>
            )}

            {/* Main Content */}
            {loading ? (
                <div className="flex justify-center items-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                </div>
            ) : error ? (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg mb-6">
                    {error}
                </div>
            ) : (
                <FileListView
                    files={files}
                    viewMode={viewMode}
                    onPreview={handlePreview}
                    onShare={handleShare}
                    onDownload={handleDownload}
                    onDelete={handleDelete}
                    showOwnership={isAdmin}
                />
            )}

            {/* Modals */}
            {showPreview && selectedFile && (
                <FilePreviewModal
                    file={selectedFile}
                    onClose={() => {
                        setShowPreview(false);
                        setSelectedFile(null);
                    }}
                    onShare={handleShare}
                />
            )}

            {showShare && selectedFile && (
                <ShareFileModal
                    file={selectedFile}
                    onClose={() => {
                        setShowShare(false);
                        setSelectedFile(null);
                    }}
                    onShare={() => {
                        fetchFiles();
                        setShowShare(false);
                        setSelectedFile(null);
                    }}
                />
            )}
        </div>
    );
};

export default FileView;