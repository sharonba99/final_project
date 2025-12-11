# Stage 1: Build the React application
FROM node:16-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
# Copy all source files and the index.html template
COPY . .
# Run the build, outputting to the default 'dist' folder
RUN npm run build 

# Stage 2: Serve the application via Nginx
FROM nginx:alpine
# Copy the custom Nginx configuration for routing
COPY nginx.conf /etc/nginx/conf.d/default.conf 
# Copy the compiled build output from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html 

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]