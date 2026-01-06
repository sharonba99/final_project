# --- Stage 1: Build the React Application ---
FROM node:18-alpine AS builder

WORKDIR /app

# Optimization: Copy package definitions first to use Docker cache
COPY package.json package-lock.json ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build 

# --- Stage 2: Serve with Nginx ---
FROM nginx:alpine

RUN apk add --no-cache curl

COPY nginx.conf /etc/nginx/conf.d/default.conf 

COPY --from=builder /app/dist /usr/share/nginx/html 

HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:80/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
