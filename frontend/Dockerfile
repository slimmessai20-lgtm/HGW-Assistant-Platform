# ── Stage 1: Build Angular ────────────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Cache npm dependencies
COPY package.json package-lock.json ./
RUN npm install --legacy-peer-deps

# Build production bundle
COPY . .
RUN npm run build -- --configuration production

# ── Stage 2: Serve with nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our nginx config
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Copy Angular build output
# Angular 17+ application builder outputs to dist/<project>/browser
COPY --from=builder /app/dist/hgw-dashboard/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
