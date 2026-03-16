# Multi-stage Dockerfile for building and serving a Vite React app

# 1) Build stage
FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Copy source and build
COPY . .
RUN yarn build

# 2) Production stage (serve static files with Nginx)
FROM nginx:1.27-alpine AS runner

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Replace default nginx config with SPA-friendly config
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

# The container listens on 80, map host 5173 -> 80 when running
EXPOSE 80

# Health check (optional, fast static check)
HEALTHCHECK CMD wget --spider -q http://localhost/ || exit 1

# Default command provided by nginx image
