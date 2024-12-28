// src/components/guest/GuestFilePreview.jsx
import React, { useState, useEffect } from 'react';
import api from '../../services/api';

const GuestFilePreview = ({ file, token }) => {
    const [preview, setPreview] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadPreview();
    }, [file]);

    const loadPreview = async () => {
        try {
            setLoading(true);

            // Get file content
            const accessToken = localStorage.getItem(`share_link_token_${token}`);
            const response = await api.get(`/api/files/${file.id}/content/`, {
                responseType: 'blob',
                headers: accessToken ? {
                    'Authorization': `Bearer ${accessToken}`
                } : {}
            });

            // Create object URL for preview
            const url = URL.createObjectURL(response.data);

            // Set preview based on file type
            if (file.mime_type.startsWith('image/')) {
                setPreview({
                    type: 'image',
                    url: url
                });
            } else if (file.mime_type === 'application/pdf') {
                setPreview({
                    type: 'pdf',
                    url: url
                });
            } else if (file.mime_type.startsWith('text/')) {
                const text = await response.data.text();
                setPreview({
                    type: 'text',
                    content: text
                });
            } else {
                setPreview({
                    type: 'unsupported'
                });
            }

            setError(null);
        } catch (err) {
            setError('Failed to load file preview');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        return () => {
            // Cleanup object URLs
            if (preview?.url) {
                URL.revokeObjectURL(preview.url);
            }
        };
    }, [preview]);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center text-red-500 py-8">
                {error}
            </div>
        );
    }

    switch (preview?.type) {
        case 'image':
            return (
                <div className="flex justify-center">
                    <img
                        src={preview.url}
                        alt={file.name}
                        className="max-w-full max-h-[500px] object-contain rounded-lg shadow-lg"
                    />
                </div>
            );

        case 'pdf':
            return (
                <div className="h-[500px] w-full">
                    <iframe
                        src={preview.url}
                        title={file.name}
                        className="w-full h-full border-0 rounded-lg shadow-lg"
                    />
                </div>
            );

        case 'text':
            return (
                <div className="bg-gray-50 p-4 rounded-lg shadow-lg">
                    <pre className="whitespace-pre-wrap font-mono text-sm">
                        {preview.content}
                    </pre>
                </div>
            );

        default:
            return (
                <div className="text-center py-8">
                    <div className="text-6xl mb-4">📄</div>
                    <p className="text-gray-600">
                        Preview not available for this file type
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                        {file.mime_type}
                    </p>
                </div>
            );
    }
};

export default GuestFilePreview;