# ============================================================
# Medical CRM - Frontend Dockerfile
# Base: node:20-alpine (multi-stage build)
#
# Stage 1: deps    → Install npm dependencies
# Stage 2: builder → Build Next.js application
# Stage 3: runner  → Minimal production image (standalone output)
#
# Kubernetes Config:
# Set BACKEND_URL env var di Kubernetes Deployment/ConfigMap
# untuk mengarahkan proxy ke backend service.
# Contoh: BACKEND_URL=http://backend-service:8000
# ============================================================

# ── Stage 1: Build Application ─────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies and build together to avoid symlink issues in older Docker versions
COPY package.json package-lock.json* ./

# Copy semua source code
COPY . .

# Jalankan npm install SETELAH COPY agar node_modules dari host (jika ada) tertimpa
RUN npm install --legacy-peer-deps

# Build Next.js (menghasilkan .next/standalone untuk output minimal)
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ── Stage 3: Production Runner ──────────────────────────────
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Buat non-root user untuk keamanan (best practice Kubernetes)
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# Copy hasil build standalone (minimal size)
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
# Buat folder public secara manual agar tidak error meskipun folder tersebut kosong/diabaikan
RUN mkdir -p public

# Ubah ownership ke non-root user
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port frontend
EXPOSE 3000

# Health check untuk Kubernetes probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD wget -q --spider http://localhost:3000 || exit 1

# Jalankan Next.js standalone server
CMD ["node", "server.js"]
