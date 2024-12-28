# frontend/Dockerfile
FROM node:18-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

RUN npm install lucide-react@0.469.0 recharts@2.15.0 chart.js@4.4.0 --save

RUN chmod -R 777 node_modules/*vite*

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 3003

# Command to run the application
CMD ["npm", "run", "dev", "--", "--host"]