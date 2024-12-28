import React from 'react';
import { Eye, Download, Share2, File, Image, FileText, Trash2 } from 'lucide-react';
import { useKeycloak } from '@react-keycloak/web';

const FileListView = ({
    files,
    onPreview,
    onShare,
    onDownload,
    onDelete,
    viewMode = 'list',  // 'list' or 'grid'
    showOwnership = false // for admin view
}) => {
    const { keycloak } = useKeycloak();
    const currentUsername = keycloak.tokenParsed?.preferred_username;
    const isAdmin = keycloak.hasRealmRole('admin');

    const getFileIcon = (mimeType) => {
        if (mimeType?.startsWith('image/')) return Image;
        if (mimeType?.startsWith('text/') || mimeType === 'application/pdf') return FileText;
        return File;
    };

    const renderListView = () => (
        <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="divide-y">
                {files.map(file => {
                    const FileIcon = getFileIcon(file.mime_type);
                    const isOwnFile = file.owner_name === currentUsername;
                    const isSharedFile = file.shared_by;

                    return (
                        <div
                            key={file.id}
                            className={`p-4 transition-colors ${showOwnership && isAdmin && !isOwnFile
                                ? 'hover:bg-blue-50 bg-blue-25'
                                : 'hover:bg-gray-50'
                                }`}
                        >
                            <div className="flex justify-between items-center">
                                <div className="flex items-center gap-3">
                                    <FileIcon className="h-5 w-5 text-gray-400" />
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <p className="font-medium text-gray-900">{file.name}</p>
                                            {showOwnership && isAdmin && (
                                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${isOwnFile
                                                    ? 'bg-green-100 text-green-800'
                                                    : 'bg-blue-100 text-blue-800'
                                                    }`}>
                                                    {isOwnFile ? 'Your File' : `Owner: ${file.owner_name}`}
                                                </span>
                                            )}
                                            {isSharedFile && (
                                                <span className="px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                                    Shared by {file.shared_by}
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-sm text-gray-500">
                                            {file.formatted_size} • {new Date(file.uploaded_at).toLocaleDateString()}
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => onPreview(file)}
                                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
                                        title="Preview"
                                    >
                                        <Eye className="h-4 w-4" />
                                    </button>
                                    {!isSharedFile && (
                                        <button
                                            onClick={() => onShare(file)}
                                            className="p-2 text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
                                            title="Share"
                                        >
                                            <Share2 className="h-4 w-4" />
                                        </button>
                                    )}
                                    <button
                                        onClick={() => onDownload(file)}
                                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-full transition-colors"
                                        title="Download"
                                    >
                                        <Download className="h-4 w-4" />
                                    </button>
                                    {(isAdmin || isOwnFile) && !isSharedFile && onDelete && (
                                        <button
                                            onClick={() => onDelete(file)}
                                            className="p-2 text-red-600 hover:bg-red-50 rounded-full transition-colors"
                                            title="Delete"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
                {files.length === 0 && (
                    <div className="p-8 text-center text-gray-500">
                        No files available
                    </div>
                )}
            </div>
        </div>
    );

    const renderGridView = () => (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {files.map(file => {
                const FileIcon = getFileIcon(file.mime_type);
                const isOwnFile = file.owner_name === currentUsername;
                const isSharedFile = file.shared_by;

                return (
                    <div key={file.id} className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-4">
                        <div className="group relative">
                            <div
                                className="aspect-square rounded-lg bg-gray-50 flex items-center justify-center mb-4 
                         group-hover:bg-gray-100 transition-colors cursor-pointer"
                                onClick={() => onPreview(file)}
                            >
                                {file.mime_type?.startsWith('image/') ? (
                                    <img
                                        src={file.file_url}
                                        alt={file.name}
                                        className="rounded-lg object-cover w-full h-full"
                                    />
                                ) : (
                                    <FileIcon className="h-16 w-16 text-gray-400" />
                                )}
                            </div>

                            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <div className="bg-white rounded-lg shadow-lg p-1 flex items-center gap-1">
                                    <button
                                        onClick={() => onPreview(file)}
                                        className="p-1 hover:bg-gray-100 rounded"
                                        title="Preview"
                                    >
                                        <Eye className="h-4 w-4 text-gray-500" />
                                    </button>
                                    {!isSharedFile && (
                                        <button
                                            onClick={() => onShare(file)}
                                            className="p-1 hover:bg-gray-100 rounded"
                                            title="Share"
                                        >
                                            <Share2 className="h-4 w-4 text-gray-500" />
                                        </button>
                                    )}
                                    <button
                                        onClick={() => onDownload(file)}
                                        className="p-1 hover:bg-gray-100 rounded"
                                        title="Download"
                                    >
                                        <Download className="h-4 w-4 text-gray-500" />
                                    </button>
                                    {(isAdmin || isOwnFile) && !isSharedFile && onDelete && (
                                        <button
                                            onClick={() => onDelete(file)}
                                            className="p-1 hover:bg-gray-100 rounded"
                                            title="Delete"
                                        >
                                            <Trash2 className="h-4 w-4 text-red-500" />
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-1">
                            <div className="flex items-center gap-2">
                                <h3 className="text-sm font-medium text-gray-900 truncate" title={file.name}>
                                    {file.name}
                                </h3>
                                {showOwnership && isAdmin && (
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${isOwnFile
                                        ? 'bg-green-100 text-green-800'
                                        : 'bg-blue-100 text-blue-800'
                                        }`}>
                                        {isOwnFile ? 'Your File' : `Owner: ${file.owner_name}`}
                                    </span>
                                )}
                                {isSharedFile && (
                                    <span className="px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-700">
                                        Shared by {file.shared_by}
                                    </span>
                                )}
                            </div>
                            <p className="text-xs text-gray-500">
                                {file.formatted_size} • {new Date(file.uploaded_at).toLocaleDateString()}
                            </p>
                        </div>
                    </div>
                );
            })}
        </div>
    );

    return viewMode === 'list' ? renderListView() : renderGridView();
};

export default FileListView;