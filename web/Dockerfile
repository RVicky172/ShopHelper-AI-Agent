# Development only: runs the Vite dev server with hot reload. Source is bind-mounted over /app.
FROM node:22-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
EXPOSE 5173
CMD ["npm", "run", "dev"]
