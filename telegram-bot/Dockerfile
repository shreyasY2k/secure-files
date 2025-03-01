FROM node:20-alpine

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy bot code
COPY bot.js ./

# Command to run the bot
CMD ["node", "bot.js"]