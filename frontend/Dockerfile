# =============================================================================
# Base Stage - Dependencies
# =============================================================================
FROM node:20-alpine AS base

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# =============================================================================
# Development Stage - Hot-Reload with Next.js Dev Server
# =============================================================================
FROM base AS development

# Install all dependencies (including dev dependencies)
RUN npm ci

# Copy source code
COPY . .

# Set development environment
ENV NODE_ENV=development

# Expose Next.js dev server port
EXPOSE 3000

# Run Next.js development server with Fast Refresh
CMD ["npm", "run", "dev"]

# =============================================================================
# Builder Stage - Build Production Assets
# =============================================================================
FROM base AS builder

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build application
RUN npm run build

# =============================================================================
# Production Stage - Optimized Runtime
# =============================================================================
FROM node:20-alpine AS production

WORKDIR /app

# Set production environment
ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built assets from builder
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Set runtime environment
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Run production server
CMD ["node", "server.js"]
