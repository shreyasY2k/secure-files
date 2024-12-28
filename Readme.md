# Secure File Sharing Platform

A secure file sharing platform built with Django, React, and Keycloak, featuring end-to-end encryption and advanced access controls.

## Features

- 🔒 End-to-end file encryption
- 🔑 Role-based authentication with Keycloak
- 👥 User role management (Admin/User)
- 🔗 Secure file sharing with expiry
- 📊 File access analytics
- 🛡️ Advanced access controls

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
├── docker-compose.yml
├── init-keycloak.sh  # Keycloak initialization script
└── README.md
```

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/shreyasY2k/secure-files
   cd secure-files
   ```

2. Start the services:
   ```bash
   docker-compose up --build
   ```
   This command will:
   - Build and start all necessary containers
   - Initialize Keycloak with default realms and users
   - Set up the database
   - Start the frontend and backend services

3. Access the services:
   - Frontend UI: http://localhost:3003
   - Keycloak Admin Console: http://localhost:3001
   - Backend API: http://localhost:3002

## Default Users

The system comes with two pre-configured users:

### Admin User
- Username: admin
- Password: Admin@123456
- Role: admin

### Regular User
- Username: user
- Password: User@123456
- Role: user

⚠️ Important: Change these credentials in production!

## Keycloak Configuration
- Admin Username: `admin`
- Admin Password: 'CDEWSXZAQ!#'
- Admin Console: http://localhost:3001

## Features in Detail

### User Authentication
- Keycloak-based authentication
- Role-based access control
- Secure session management

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

## Development Components

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
- Customizable authentication flows

## Next Steps

### Adding SSL/HTTPS
SSL/HTTPS support is planned for the next update. This will include:
- Certificate generation
- HTTPS configuration for all services
- Secure cookie handling

## Troubleshooting

### Common Issues

1. Keycloak Connection Issues
   - Ensure all services are up: `docker-compose ps`
   - Check Keycloak logs: `docker-compose logs keycloak`
   - Wait for Keycloak initialization to complete

2. File Upload Issues
   - Check storage permissions
   - Verify file size limits
   - Check backend logs: `docker-compose logs backend`

3. Authorization Issues
   - Verify user roles in Keycloak admin console
   - Check token configuration
   - Clear browser cache and cookies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request


## Support

For issues and feature requests, please use the GitHub issue tracker.