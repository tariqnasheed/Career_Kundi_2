# =============================================================================
# Careerkundi Frontend — Production Dockerfile
# Stage 1 builds the static Vite bundle. Stage 2 serves it via nginx — a
# tiny, battle-tested static file server with gzip + caching built in.
# =============================================================================

FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine AS runtime
# Single-page-app routing config: any unknown path falls back to index.html
# so client-side React Router can take over.
COPY infra-spa.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=5s --retries=10 \
    CMD wget --spider -q http://localhost:80 || exit 1
CMD ["nginx", "-g", "daemon off;"]
