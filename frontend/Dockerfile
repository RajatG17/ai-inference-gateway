FROM node:20-alpine AS builder

WORKDIR /app

# Install deps
COPY package.json package-lock.json ./
RUN npm ci

# Copy source
COPY . .

# Build Next.js app
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]

# ---------- Production Stage ----------
# FROM node:20-alpine

# WORKDIR /app

# ENV NODE_ENV=production

# # Only copy necessary files
# COPY --from=builder /app/package.json ./
# COPY --from=builder /app/package-lock.json ./
# RUN npm ci --omit=dev

# COPY --from=builder /app/.next ./.next
# COPY --from=builder /app/public ./public
# COPY --from=builder /app/next.config.ts ./next.config.ts

# EXPOSE 3000

# CMD ["npm", "start"]