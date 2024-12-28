import React, { useState, useEffect } from 'react';
import { X, Download, Share2, FileText, Image, File } from 'lucide-react';
import api from '../../../services/api';
import { decryptFile } from '../../../utils/encryption';

const PDFPreview = ({ url }) => {
    return (
        <div className="w-full h-[600px] rounded-lg shadow-lg overflow-hidden">
            <object
                data={url}
                type="application/pdf"
                className="w-full h-full"
            >
                <embed
                    src={url}
                    type="application/pdf"
                    className="w-full h-full"
                />
            </object>
        </div>
    );
};

const FilePreviewModal = ({ file, onClose, onShare }) => {
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadPreview();
        return () => {
            if (preview?.url) {
                URL.revokeObjectURL(preview.url);
            }
        };
    }, [file]);

    const loadPreview = async () => {
        try {
            setLoading(true);
            const response = await api.get(`/api/files/${file.id}/content/`, {
                responseType: 'arraybuffer'
            });

            let content = response.data;
            if (file.encryption_key) {
                content = await decryptFile(
                    response.data,
                    file.encryption_key,
                    file.encryption_iv
                );
            }

            const handleContent = async () => {
                if (file.mime_type.startsWith('image/')) {
                    const blob = new Blob([content], { type: file.mime_type });
                    setPreview({
                        type: 'image',
                        url: URL.createObjectURL(blob),
                        icon: Image
                    });
                } else if (file.mime_type === 'application/pdf') {
                    const blob = new Blob([content], { type: 'application/pdf' });
                    setPreview({
                        type: 'pdf',
                        url: URL.createObjectURL(blob),
                        icon: FileText
                    });
                } else if (file.mime_type.startsWith('text/')) {
                    const text = new TextDecoder().decode(content);
                    setPreview({
                        type: 'text',
                        content: text,
                        icon: FileText
                    });
                } else {
                    setPreview({
                        type: 'unsupported',
                        icon: File
                    });
                }
            };

            await handleContent();
            setError(null);
        } catch (err) {
            console.error('Preview error:', err);
            setError('Failed to load file preview');
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async () => {
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

    const PreviewIcon = preview?.icon || File;

    const renderPreview = () => {
        if (preview?.type === 'pdf') {
            return (
                <div className="text-center">
                    <div className="bg-gray-50 p-6 rounded-lg mb-4">
                        <FileText className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                        <p className="text-gray-600 text-lg mb-2">
                            PDF preview is not available in the browser
                        </p>
                        <p className="text-sm text-gray-500">
                            Please download the file to view its contents
                        </p>
                    </div>
                    <button
                        onClick={handleDownload}
                        className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors inline-flex items-center gap-2"
                    >
                        <Download className="h-4 w-4" />
                        Download PDF
                    </button>
                </div>
            );
        }

        if (preview?.type === 'image') {
            return (
                <div className="flex justify-center">
                    <img
                        src={preview.url}
                        alt={file.name}
                        className="max-w-full max-h-[600px] object-contain rounded-lg shadow-lg"
                    />
                </div>
            );
        }

        if (preview?.type === 'text') {
            return (
                <pre className="whitespace-pre-wrap font-mono text-sm bg-gray-50 p-6 rounded-lg shadow-inner">
                    {preview.content}
                </pre>
            );
        }

        return (
            <div className="text-center py-12">
                <File className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600 text-lg">
                    Preview not available for this file type
                </p>
                <p className="text-sm text-gray-500 mt-2">
                    {file.mime_type}
                </p>
            </div>
        );
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
                {/* Header */}
                <div className="p-4 border-b flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <PreviewIcon className="h-5 w-5 text-gray-500" />
                        <div>
                            <h3 className="text-lg font-semibold text-gray-900">{file.name}</h3>
                            <p className="text-sm text-gray-500">{file.formatted_size}</p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                    >
                        <X className="h-5 w-5 text-gray-500" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4 overflow-auto max-h-[calc(90vh-8rem)]">
                    {loading ? (
                        <div className="flex justify-center items-center h-64">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                        </div>
                    ) : error ? (
                        <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center justify-center">
                            {error}
                        </div>
                    ) : (
                        <div className="preview-content">
                            {renderPreview()}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t bg-gray-50">
                    <div className="flex justify-end gap-3">
                        <button
                            onClick={() => onShare(file)}
                            className="px-4 py-2 flex items-center gap-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                            <Share2 className="h-4 w-4" />
                            Share
                        </button>
                        <button
                            onClick={handleDownload}
                            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
                        >
                            <Download className="h-4 w-4" />
                            Download
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FilePreviewModal;