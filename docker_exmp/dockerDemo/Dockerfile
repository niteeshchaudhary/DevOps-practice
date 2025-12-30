# React Dockerfile
FROM node:16-alpine

WORKDIR /app

# Copy and install dependencies
COPY package.json package-lock.json ./
RUN npm install 

# Copy the rest of the application code
COPY . .

# Build the React application
RUN npm run build

# Install serve to serve the built application
RUN npm install  -g serve

# Expose the port that serve will use
EXPOSE 3000

# Serve the application
CMD ["serve", "-s", "dist"]
