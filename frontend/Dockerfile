FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies separately for layer caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy full application code & build Next.js
COPY . .
RUN npm run build

# Set up lightweight production runner
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production

# Copy required artifacts from the builder
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
ENV PORT 3000

CMD ["npm", "start"]
