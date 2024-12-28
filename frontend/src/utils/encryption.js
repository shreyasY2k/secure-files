export const generateEncryptionKey = async () => {
    // Generate a random 256-bit (32-byte) key
    const key = await window.crypto.subtle.generateKey(
        {
            name: "AES-GCM",
            length: 256
        },
        true,
        ["encrypt", "decrypt"]
    );

    // Export the key to raw format
    const exportedKey = await window.crypto.subtle.exportKey("raw", key);
    return new Uint8Array(exportedKey);
};

export const encryptFile = async (file, keyBuffer) => {
    try {
        // Generate a random 12-byte IV (initialization vector)
        const iv = window.crypto.getRandomValues(new Uint8Array(12));

        // Import the raw key buffer for use with SubtleCrypto
        const key = await window.crypto.subtle.importKey(
            "raw",
            keyBuffer,
            {
                name: "AES-GCM",
                length: 256
            },
            false,
            ["encrypt"]
        );

        // Read the file as ArrayBuffer
        const fileData = await file.arrayBuffer();

        // Encrypt the file data
        const encryptedData = await window.crypto.subtle.encrypt(
            {
                name: "AES-GCM",
                iv: iv,
                tagLength: 128
            },
            key,
            fileData
        );

        // Combine IV and encrypted data
        const combinedData = new Uint8Array(iv.length + encryptedData.byteLength);
        combinedData.set(iv, 0);
        combinedData.set(new Uint8Array(encryptedData), iv.length);

        // Create a new Blob with the encrypted data
        return new Blob([combinedData], { type: 'application/octet-stream' });
    } catch (error) {
        console.error('Encryption error:', error);
        throw new Error('Failed to encrypt file');
    }
};

export const decryptFile = async (encryptedBlob, keyBuffer) => {
    try {
        // Read the encrypted data
        const encryptedData = await encryptedBlob.arrayBuffer();
        const encryptedArray = new Uint8Array(encryptedData);

        // Extract IV and encrypted content
        const iv = encryptedArray.slice(0, 12);
        const content = encryptedArray.slice(12);

        // Import the key
        const key = await window.crypto.subtle.importKey(
            "raw",
            keyBuffer,
            {
                name: "AES-GCM",
                length: 256
            },
            false,
            ["decrypt"]
        );

        // Decrypt the data
        const decryptedData = await window.crypto.subtle.decrypt(
            {
                name: "AES-GCM",
                iv: iv,
                tagLength: 128
            },
            key,
            content
        );

        return new Blob([decryptedData], { type: encryptedBlob.type });
    } catch (error) {
        console.error('Decryption error:', error);
        throw new Error('Failed to decrypt file');
    }
};

// Helper function to convert base64 to array buffer
function base64ToArrayBuffer(base64String) {
    // Ensure we're working with a string
    base64String = String(base64String);

    // Convert base64url to base64 by replacing URL-safe chars
    base64String = base64String.replace(/-/g, '+').replace(/_/g, '/');

    // Add padding if needed
    while (base64String.length % 4) {
        base64String += '=';
    }

    // Decode base64 to binary string
    const binaryString = atob(base64String);

    // Convert binary string to Uint8Array
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }

    return bytes.buffer;
}

export async function decryptFernetData(encryptedData, keyBase64) {
    try {
        console.log('Starting decryption...');
        console.log('Key (base64):', keyBase64);

        // Ensure we're working with Uint8Array
        const data = encryptedData instanceof Uint8Array ?
            encryptedData :
            new Uint8Array(base64ToArrayBuffer(encryptedData));

        // Log the structure
        console.log('Data length:', data.length);
        console.log('First byte (version):', data[0]);
        console.log('First 32 bytes:', Array.from(data.slice(0, 32)));

        // Extract parts
        const version = data[0];
        const timestamp = data.slice(1, 9);
        const iv = data.slice(9, 25);
        const ciphertext = data.slice(25, -32);
        const hmac = data.slice(-32);

        // Log extracted parts
        console.log('Extracted parts:');
        console.log('- IV length:', iv.length);
        console.log('- Ciphertext length:', ciphertext.length);
        console.log('- HMAC length:', hmac.length);

        // Convert key from base64 to buffer
        const keyBuffer = base64ToArrayBuffer(keyBase64);
        console.log('Key buffer length:', keyBuffer.byteLength);

        // Import the key for decryption
        const key = await window.crypto.subtle.importKey(
            "raw",
            keyBuffer,
            { name: "AES-CBC", length: 256 },
            false,
            ["decrypt"]
        );

        // Perform decryption
        const decryptedBuffer = await window.crypto.subtle.decrypt(
            {
                name: "AES-CBC",
                iv: iv
            },
            key,
            ciphertext
        );

        // Convert decrypted buffer to Uint8Array
        return new Uint8Array(decryptedBuffer);

    } catch (error) {
        console.error('Decryption error:', error);
        console.error('Stack:', error.stack);
        throw error;
    }
}

export async function handleEncryptedDownload(response, file) {
    try {
        // Get encryption key from headers
        const encryptionKey = response.headers.get('x-encryption-key');
        console.log('Encryption key from headers:', encryptionKey);

        if (encryptionKey) {
            console.log('No encryption key found, returning raw data');
            return response.data;
        }

        // Convert blob to array buffer
        const encryptedBuffer = await response.data.arrayBuffer();
        const encryptedArray = new Uint8Array(encryptedBuffer);

        // Decrypt the data
        const decryptedData = await decryptFernetData(encryptedArray, encryptionKey);

        // Create a new blob with the decrypted data
        return new Blob([decryptedData], {
            type: file.mime_type || 'application/octet-stream'
        });

    } catch (error) {
        console.error('Download processing error:', error);
        throw error;
    }
}