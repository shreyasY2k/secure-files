import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { getFiles, uploadFile, shareFile, generateShareLink } from '../services/api';

const initialState = {
    files: [],
    status: 'idle',
    error: null,
};

export const fetchFiles = createAsyncThunk(
    'files/fetchFiles',
    async () => {
        const response = await getFiles();
        return response;
    }
);

export const uploadNewFile = createAsyncThunk(
    'files/uploadFile',
    async ({ file, encryptionKey }) => {
        const response = await uploadFile(file, encryptionKey);
        return response;
    }
);

export const shareFileWithUser = createAsyncThunk(
    'files/shareFile',
    async ({ fileId, userId, permissions }) => {
        const response = await shareFile(fileId, userId, permissions);
        return response;
    }
);

const filesSlice = createSlice({
    name: 'files',
    initialState,
    reducers: {},
    extraReducers: (builder) => {
        builder
            .addCase(fetchFiles.pending, (state) => {
                state.status = 'loading';
            })
            .addCase(fetchFiles.fulfilled, (state, action) => {
                state.status = 'succeeded';
                state.files = action.payload;
            })
            .addCase(fetchFiles.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.error.message;
            })
            .addCase(uploadNewFile.fulfilled, (state, action) => {
                state.files.push(action.payload);
            })
            .addCase(shareFileWithUser.fulfilled, (state, action) => {
                const index = state.files.findIndex(file => file.id === action.payload.fileId);
                if (index !== -1) {
                    state.files[index] = { ...state.files[index], ...action.payload };
                }
            });
    },
});

export default filesSlice.reducer;