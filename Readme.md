# Secure File Sharing Platform

A secure file sharing platform built with Django, React, and Keycloak, featuring end-to-end encryption and advanced access controls.

## Features

- 🔒 End-to-end file encryption
- 🔑 Two-factor authentication (TOTP)
- 👥 User role management (Admin/User)
- 🔗 Secure file sharing with expiry
- 📊 File access analytics
- 🛡️ HTTPS everywhere

## Prerequisites

- Docker and Docker Compose
- Windows/Linux/MacOS
- Modern web browser
- Git

## Project Structure

```tree
secure-files/
├── backend/          # Django backend
├── frontend/         # React frontend
├── keycloak/         # Keycloak themes
│   └── themes/
│       └── secure-files/
├── certs/            # SSL certificates (generated)
├── docker-compose.yaml
├── init-keycloak.sh
└── README.md

## Quick Start

1. Clone the repository:
   git clone https://github.com/shreyasY2k/secure-files
   cd secure-files

2. Create necessary directories:
   mkdir -p backend frontend keycloak/themes/secure-files certs

3. Start the services:
   docker-compose up -d

4. Install the CA certificate:

   Windows (Run PowerShell as Administrator):
   Import-Certificate -FilePath .\certs\ca.crt -CertStoreLocation Cert:\LocalMachine\Root

   MacOS:
   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ./certs/ca.crt

   Linux:
   sudo cp ./certs/ca.crt /usr/local/share/ca-certificates/
   sudo update-ca-certificates

5. Access the services:
   - Frontend: https://localhost:3003
   - Backend API: https://localhost:3002
   - Keycloak: https://localhost:3001

## Default Credentials

### Admin User

- Username: admin
- Password: admin123
- Email: admin@securefile.local

### Regular User

- Username: user
- Password: user123
- Email: user@securefile.local

⚠️ Important: Change these credentials in production!

## Features in Detail

### File Encryption

- Files are encrypted before storage
- Each file has a unique encryption key
- Keys are securely managed

### User Authentication

- Two-factor authentication using TOTP
- Role-based access control
- Secure password policy enforcement

### File Sharing

- Secure share links with expiry
- Access count limits
- Password protection option
- User-to-user direct sharing

### Admin Features

- User management
- Storage quota management
- Access statistics
- System monitoring

## Development

### Backend (Django)

- REST API with Django REST framework
- PostgreSQL database
- Secure file storage

### Frontend (React)

- Modern React with Hooks
- Tailwind CSS for styling
- Real-time updates

### Security (Keycloak)

- OAuth 2.0 / OpenID Connect
- Role-based access control
- Custom theme support

## Environment Variables

Required environment variables in Docker Compose:
KEYCLOAK_ADMIN: admin
KEYCLOAK_ADMIN_PASSWORD: admin
FRONTEND_URL: https://localhost:3003
SECURE_FILES_ADMIN_USERNAME: admin
SECURE_FILES_ADMIN_PASSWORD: admin123
SECURE_FILES_USER_USERNAME: user
SECURE_FILES_USER_PASSWORD: user123

## Production Deployment

For production deployment:

1. Change all default passwords
2. Use proper SSL certificates
3. Configure proper email settings
4. Set secure password policies
5. Enable email verification
6. Configure backup strategy
7. Set up monitoring

## Troubleshooting

### Common Issues

1. Certificate Errors

   - Ensure CA certificate is properly installed
   - Check certificate paths in docker-compose.yaml

2. Keycloak Connection Issues

   - Wait for Keycloak initialization
   - Check if ports are free
   - Verify Keycloak configuration

3. File Upload Issues
   - Check storage permissions
   - Verify file size limits
   - Check encryption settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker.
```
