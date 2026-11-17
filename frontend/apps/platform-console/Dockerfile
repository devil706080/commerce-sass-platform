FROM node:26-alpine AS dependencies
WORKDIR /workspace
RUN npm install --global pnpm@12.19.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/platform-console/package.json ./apps/platform-console/package.json
RUN pnpm install --frozen-lockfile --filter @commerce-saas/platform-console...

FROM node:26-alpine AS build
WORKDIR /workspace
ARG NEXT_PUBLIC_KEYCLOAK_URL
ARG NEXT_PUBLIC_KEYCLOAK_REALM
ARG NEXT_PUBLIC_KEYCLOAK_CLIENT_ID
ARG NEXT_PUBLIC_CONTROL_API_URL
ENV NEXT_PUBLIC_KEYCLOAK_URL=$NEXT_PUBLIC_KEYCLOAK_URL \
    NEXT_PUBLIC_KEYCLOAK_REALM=$NEXT_PUBLIC_KEYCLOAK_REALM \
    NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=$NEXT_PUBLIC_KEYCLOAK_CLIENT_ID \
    NEXT_PUBLIC_CONTROL_API_URL=$NEXT_PUBLIC_CONTROL_API_URL
RUN npm install --global pnpm@12.19.0
COPY --from=dependencies /workspace/node_modules ./node_modules
COPY --from=dependencies /workspace/apps/platform-console/node_modules ./apps/platform-console/node_modules
COPY . .
RUN pnpm --filter @commerce-saas/platform-console typecheck && pnpm --filter @commerce-saas/platform-console build

FROM node:26-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3000
RUN addgroup -S app && adduser -S app -G app
COPY --from=build --chown=app:app /workspace/apps/platform-console/.next/standalone ./
COPY --from=build --chown=app:app /workspace/apps/platform-console/.next/static ./apps/platform-console/.next/static
USER app
EXPOSE 3000
CMD ["node", "apps/platform-console/server.js"]
