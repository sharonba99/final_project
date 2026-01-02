# Build react app
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json ./
RUN npm install

COPY . .

# Test
RUN npm test -- --watchAll=false

RUN npm run build 

# Serve app with nginx server
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf 

COPY --from=builder /app/dist /usr/share/nginx/html 

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]