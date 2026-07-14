FROM node:22-alpine AS dependencies
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

FROM dependencies AS builder
ARG NEXT_PUBLIC_BERRYBRAIN_BASE_PATH=/berrybrain
ARG NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX=/berrybrain
ENV NEXT_PUBLIC_BERRYBRAIN_BASE_PATH=$NEXT_PUBLIC_BERRYBRAIN_BASE_PATH \
    NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX=$NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX \
    NEXT_TELEMETRY_DISABLED=1
COPY apps/web ./
RUN npm run build

FROM node:22-alpine AS runtime
ARG NEXT_PUBLIC_BERRYBRAIN_BASE_PATH=/berrybrain
ARG NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX=/berrybrain
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000 \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_BERRYBRAIN_BASE_PATH=$NEXT_PUBLIC_BERRYBRAIN_BASE_PATH \
    NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX=$NEXT_PUBLIC_BERRYBRAIN_ASSET_PREFIX
WORKDIR /app
COPY --chown=node:node --from=builder /app/.next/standalone ./
COPY --chown=node:node --from=builder /app/.next/static ./.next/static
COPY --chown=node:node --from=builder /app/public ./public
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx

EXPOSE 3000
USER node
CMD ["node", "server.js"]
