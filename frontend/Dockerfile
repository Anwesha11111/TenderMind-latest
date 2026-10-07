# ────────────────────────────────────────────────────────────────────────
# TenderMind Frontend Dockerfile
# React + TypeScript + Vite
# ────────────────────────────────────────────────────────────────────────

<<<<<<< HEAD
FROM node:22-alpine
=======
FROM node:20-alpine
>>>>>>> 4e831edd2a8d727fe267b4289bffc197d5ecf0a6

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy frontend code
COPY . .

# Expose port
EXPOSE 3000

# Default command (development server)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
