# Use a small Node image
FROM node:18-alpine
WORKDIR /app

# Copy package and install dependencies
COPY package.json package-lock.json ./
RUN npm install --production

# Copy the rest of the code
COPY . .

# Expose port and launch
EXPOSE 3000
CMD ["npm", "start"]