// src/utils/fileEncryption.js

/**
 * Generates a random encryption key
 * @returns {Uint8Array} 32-byte encryption key
 */
export const generateEncryptionKey = async () => {
    const key = await window.crypto.subtle.generateKey(
      {
        name: 'AES-GCM',
        length: 256
      },
      true,
      ['encrypt', 'decrypt']
    );
    const rawKey = await window.crypto.subtle.exportKey('raw', key);
    return new Uint8Array(rawKey);
  };
  
  /**
   * Encrypts a file before upload
   * @param {File} file - The file to encrypt
   * @returns {Promise<{encryptedFile: Blob, key: string}>}
   */
  export const encryptFile = async (file) => {
    try {
      // Generate a random encryption key
      const rawKey = await generateEncryptionKey();
      
      // Generate a random IV
      const iv = window.crypto.getRandomValues(new Uint8Array(12));
      
      // Import the key for encryption
      const key = await window.crypto.subtle.importKey(
        'raw',
        rawKey,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt']
      );
  
      // Read the file as ArrayBuffer
      const fileData = await file.arrayBuffer();
      
      // Encrypt the file data
      const encryptedData = await window.crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        key,
        fileData
      );
  
      // Combine IV and encrypted data
      const combinedData = new Uint8Array(iv.length + encryptedData.byteLength);
      combinedData.set(iv, 0);
      combinedData.set(new Uint8Array(encryptedData), iv.length);
  
      // Convert the key to base64 for transmission
      const keyBase64 = btoa(String.fromCharCode(...rawKey));
  
      // Create a new blob with the encrypted data
      const encryptedBlob = new Blob([combinedData], { type: 'application/octet-stream' });
  
      return {
        encryptedFile: encryptedBlob,
        key: keyBase64
      };
    } catch (error) {
      console.error('Encryption error:', error);
      throw new Error('Failed to encrypt file');
    }
  };
  
  /**
   * Decrypts a downloaded file
   * @param {Blob} encryptedBlob - The encrypted file blob
   * @param {string} keyBase64 - Base64 encoded encryption key
   * @param {string} mimeType - Original file MIME type
   * @returns {Promise<Blob>} Decrypted file blob
   */
  export const decryptFile = async (encryptedBlob, keyBase64, mimeType) => {
    try {
      // Convert base64 key back to Uint8Array
      const keyData = Uint8Array.from(atob(keyBase64), c => c.charCodeAt(0));
      
      // Import the key for decryption
      const key = await window.crypto.subtle.importKey(
        'raw',
        keyData,
        { name: 'AES-GCM', length: 256 },
        false,
        ['decrypt']
      );
  
      // Read the encrypted data
      const encryptedData = await encryptedBlob.arrayBuffer();
      const encryptedArray = new Uint8Array(encryptedData);
  
      // Extract IV and encrypted content
      const iv = encryptedArray.slice(0, 12);
      const content = encryptedArray.slice(12);
  
      // Decrypt the data
      const decryptedData = await window.crypto.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        key,
        content
      );
  
      // Create a new blob with the decrypted data and original mime type
      return new Blob([decryptedData], { type: mimeType || 'application/octet-stream' });
    } catch (error) {
      console.error('Decryption error:', error);
      throw new Error('Failed to decrypt file');
    }
  };