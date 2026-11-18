FROM node:26-alpine AS dependencies
WORKDIR /workspace
RUN npm install --global pnpm@12.19.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/tenant-admin/package.json ./apps/tenant-admin/package.json
RUN pnpm install --frozen-lockfile --filter @commerce-saas/tenant-admin...
FROM node:26-alpine AS build
WORKDIR /workspace
ARG NEXT_PUBLIC_KEYCLOAK_URL ARG NEXT_PUBLIC_KEYCLOAK_REALM ARG NEXT_PUBLIC_KEYCLOAK_CLIENT_ID ARG NEXT_PUBLIC_CATALOGUE_API_URL ARG NEXT_PUBLIC_TENANT_ADMIN_NAME ARG NEXT_PUBLIC_TENANT_ADMIN_PRIMARY ARG NEXT_PUBLIC_TENANT_ADMIN_PRIMARY_DARK ARG NEXT_PUBLIC_TENANT_ADMIN_ACCENT
ENV NEXT_PUBLIC_KEYCLOAK_URL=$NEXT_PUBLIC_KEYCLOAK_URL NEXT_PUBLIC_KEYCLOAK_REALM=$NEXT_PUBLIC_KEYCLOAK_REALM NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=$NEXT_PUBLIC_KEYCLOAK_CLIENT_ID NEXT_PUBLIC_CATALOGUE_API_URL=$NEXT_PUBLIC_CATALOGUE_API_URL NEXT_PUBLIC_TENANT_ADMIN_NAME=$NEXT_PUBLIC_TENANT_ADMIN_NAME NEXT_PUBLIC_TENANT_ADMIN_PRIMARY=$NEXT_PUBLIC_TENANT_ADMIN_PRIMARY NEXT_PUBLIC_TENANT_ADMIN_PRIMARY_DARK=$NEXT_PUBLIC_TENANT_ADMIN_PRIMARY_DARK NEXT_PUBLIC_TENANT_ADMIN_ACCENT=$NEXT_PUBLIC_TENANT_ADMIN_ACCENT
RUN npm install --global pnpm@12.19.0
COPY --from=dependencies /workspace/node_modules ./node_modules
COPY --from=dependencies /workspace/apps/tenant-admin/node_modules ./apps/tenant-admin/node_modules
COPY . .
RUN pnpm --filter @commerce-saas/tenant-admin typecheck && pnpm --filter @commerce-saas/tenant-admin build
FROM node:26-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3001
RUN addgroup -S app && adduser -S app -G app
COPY --from=build --chown=app:app /workspace/apps/tenant-admin/.next/standalone ./
COPY --from=build --chown=app:app /workspace/apps/tenant-admin/.next/static ./apps/tenant-admin/.next/static
USER app
EXPOSE 3001
CMD ["node","apps/tenant-admin/server.js"]
