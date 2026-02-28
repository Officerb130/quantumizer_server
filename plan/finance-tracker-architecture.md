# Personal Finance Tracker — Architecture Plan

**Generated:** 2026-02-28 (Revised)

---

## 1. Goals

- Single Linux VM deployment via Docker Compose
- Minimal containers (2 in Phase 1: `app` + `db`)
- Mobile-friendly versioned REST API (`/api/v1`)
- Optimised for agentic (AI-assisted) development
- Safe, incremental evolution without rewrite

---

## 2. High-Level Architecture

```
Internet
   |
[Optional: Nginx reverse proxy — Phase 2]
   |
Next.js App Container
  ├── Web UI (React, App Router)
  ├── tRPC router (UI ↔ backend, type-safe)
  ├── REST API /api/v1 (mobile + external clients)
  └── Prisma (migrations + queries)
   |
PostgreSQL Container
```

**Two API layers, one backend:**
- **tRPC** — used exclusively by the Next.js frontend. Zero DTO boilerplate, full end-to-end types.
- **REST `/api/v1`** — stable, versioned, OpenAPI-documented. Used by mobile apps and future external clients.

Both layers call the same service layer. No business logic lives in routers.

---

## 3. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14+ (App Router, React, TypeScript) |
| UI → Backend | tRPC v11 |
| Mobile/External API | Next.js Route Handlers (REST) |
| Validation | Zod (shared between tRPC + REST DTOs) |
| ORM | Prisma |
| Database | PostgreSQL 16 |
| Auth | JWT — access token (15min) + refresh token (30 days, HttpOnly cookie) |
| Hosting | Linux VM + Docker Compose |
| API Docs | OpenAPI 3.1 (auto-generated from Zod schemas via `zod-openapi`) |
| Classifier — regex | Native `RegExp` (no extra library; JS regex supports all required patterns) |
| Classifier — LRU cache | `lru-cache` npm package (v10+, TypeScript-native, zero deps) |
| CSV parsing | `csv-parse` npm package (streaming, handles quoted fields and edge cases) |

---

## 4. Repository Structure

```
src/
  app/                        # Next.js UI pages and layouts
  api/
    v1/                       # REST handlers (mobile/external)
      auth/
      transactions/
      groups/
      classes/
      classifiers/
      sources/
      imports/
  trpc/                       # tRPC router definitions (UI only)
    routers/
      transactions.ts
      groups.ts
      classes.ts
      classifiers.ts
      sources.ts
    index.ts
  domain/                     # Pure business logic, no I/O
    transaction.ts            # rules: amount sign convention, dedup key
    classification.ts         # rules: regex matching, LRU cache logic
    import.ts                 # rules: CSV normalisation, file hash dedup
  services/                   # Orchestration — calls domain + repositories
    transactionService.ts
    classificationService.ts  # classification engine: seeding + re-classify
    importService.ts
    authService.ts
  repositories/               # Prisma queries only, no business logic
    transactionRepository.ts
    classRepository.ts
    groupRepository.ts
    sourceRepository.ts
    classifierRepository.ts
  dtos/                       # Zod schemas — source of truth for validation
    transaction.dto.ts        # shared between tRPC + REST
    class.dto.ts
    group.dto.ts
    import.dto.ts
  lib/
    prisma.ts                 # singleton Prisma client
    auth.ts                   # JWT encode/decode/verify
    errors.ts                 # typed error classes (AppError, NotFoundError, etc.)
    openapi.ts                # OpenAPI doc generation
    classifierEngine.ts       # regex matching engine + LRU cache
prisma/
  schema.prisma
  seed.ts                     # seeds types, groups, classes from JSON config
  migrations/
data/
  general/
    type_defaults.json        # transaction type seed data
    group_defaults.json       # group seed data
    class_defaults.json       # class + classifier rule seed data
    client_defaults.json      # initial user/client seed data
docker/
  app.Dockerfile
docker-compose.yml
docker-compose.override.yml   # local dev overrides
.env.example
```

### Layer Rules (strict — agents must not cross these)

| Layer | Can call | Cannot call |
|---|---|---|
| API / tRPC router | Services, DTOs | Repositories, Domain directly |
| Services | Domain, Repositories | API layer |
| Domain | Nothing (pure functions) | Services, Repositories, Prisma |
| Repositories | Prisma only | Services, Domain, API |

---

## 5. Data Model

### Full Entity List

```
User                    // login credential + type; maps to "client" in source system
TransactionType         // Debit Normal, Credit Normal, Debit Abnormal, Credit Abnormal
TransactionGroup        // coarse spending category: Food, Transport, Utilities, ...
TransactionClass        // fine-grained category; belongs to one Group + one Type
ClassifierRule          // regex rule (+ optional value/date constraints) for auto-classification
TransactionSource       // named import source (e.g. "ANZ Cheque"); belongs to User
TransactionSourceFile   // imported file record (filename + hash); used for dedup
Transaction             // single bank transaction; classified into a TransactionClass
RefreshToken            // JWT refresh token store for single-use enforcement
```

### Transaction Type Values (seeded, not user-editable)

| Name | Hidden |
|---|---|
| Debit Normal | false |
| Credit Normal | false |
| Debit Abnormal | true |
| Credit Abnormal | true |

### Transaction Group Values (seeded, user-extensible)

Undefined Debit, Undefined Credit, Food, Health, Goods, Services, Entertainment, Education,
Loans, Income, Govt Welfare, Transport, Utilities, Insurance, Cash, Misc Debit, Misc Credit,
Tax, Investment, Holiday, Renovation

### Classification Engine

Transactions are auto-classified on import and on periodic re-classification runs.

```
classificationService.reclassify(fromDate):
  → Load all ClassifierRules from DB (grouped by class)
  → Initialise LRU cache (capacity 200, keyed by regex pattern)
  → Fetch all Transactions where date >= fromDate
  → For each Transaction:
      → description.toUpperCase() for case-insensitive matching
      → Check LRU cache first (avoids re-evaluating rules for repeated descriptions)
      → If cache miss:
          Pass 1 — constrained rules (value, valueMax, valueMin, or date set):
            → Test regex against description
            → If regex matches AND all constraints pass → assign class, cache hit
          Pass 2 — regex-only rules (no value/date constraints):
            → Test regex against description
            → If regex matches → assign class, cache hit
          Pass 3 — fallback:
            → amount < 0  → assign "Undefined Debit" class
            → amount >= 0 → assign "Undefined Credit" class
      → UPDATE Transaction SET classId = resolved classId
```

**Why two passes?** Constrained rules are more specific (e.g. same merchant but different amounts). They must be evaluated before broad regex-only rules to avoid the general pattern winning first.

**LRU cache:** Implemented with `lru-cache` (npm). Key = regex string. Value = the matched `ClassifierRule` checker. Capacity 200 covers the long tail of repeated description strings without excessive memory use. Cache is per-reclassify call (not persistent across requests).

**ClassifierRule matching fields:**
- `regex` — case-insensitive pattern matched against `Transaction.description.toUpperCase()`
- `value` — optional: exact amount match (strict equality after rounding)
- `valueMin` / `valueMax` — optional: amount range (uses `Math.abs(amount)`)
- `date` — optional: exact date string match (`YYYY-MM-DD`)

### Import Pipeline

#### File Naming Convention

CSV files must be named `{source}_{YYYY-MM}.csv`, e.g. `ANZ_2024-01.csv`.

- Everything before the first `_` is treated as the **source name** and used to look up or auto-create a `TransactionSource` record for the authenticated user.
- The `YYYY-MM` portion is metadata only — it does not constrain which dates the file may contain.

#### CSV Format

| Column | Position | Format | Notes |
|---|---|---|---|
| Date | 0 | `DD/MM/YYYY` | Parsed to `YYYY-MM-DD` for storage |
| Amount | 1 | Float string | May be negative (debit) or positive (credit); stored as `Decimal(12,2)` |
| Description | 2 | String | Quotes stripped; used for classification regex matching |

Rows with fewer than 3 columns are silently skipped (header rows, blank lines).

#### Processing Flow

```
User uploads {source}_{YYYY-MM}.csv via POST /imports
  → Compute MD5 hash of raw file content
  → Resolve source name (text before first "_" in filename)
  → Look up or create TransactionSource for (name, userId)
  → Check TransactionSourceFile for (filename, userId):
      - If found AND hash matches: reject — file already processed (idempotent)
      - If found AND hash differs: allow — file was updated, process new rows only
      - If not found: allow — new file
  → Parse CSV rows (skip rows with < 3 columns)
  → For each row:
      → Parse date: DD/MM/YYYY → YYYY-MM-DD
      → Parse amount: string → Decimal, round to 2dp
      → Strip single-quotes from description
      → Dedup check: (date, description, amount, sourceId) unique in DB
          - If duplicate: skip (count as skipped)
          - If new: insert Transaction (classId = null)
  → Upsert TransactionSourceFile (filename, userId, newHash)
  → Trigger classification from earliest inserted transaction date
  → Return: { inserted, skipped, sourceId, sourceFileId }
```

**Idempotency:** Re-uploading the same file (same hash) is rejected cleanly. Re-uploading an updated file (different hash) is safe — only genuinely new rows are inserted.

**Classification trigger:** After import, `classificationService.reclassify(fromDate)` is called with the date of the earliest newly inserted transaction, so only the affected window is re-processed.

`TransactionSourceFile` rows are **never deleted**. File hash history is permanent.

### Key Data Rules

- Money fields: `Decimal(12, 2)` — never Float
- `Transaction.amount` is stored as-is from bank data; `TransactionClass.type` carries the semantic direction (debit/credit)
- Hidden transaction types (`hidden = true`) are excluded from default reporting queries

---

## 6. Prisma Schema

```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model User {
  id           String   @id @default(cuid())
  name         String   @unique
  passwordHash String
  type         String
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  sources       TransactionSource[]
  sourceFiles   TransactionSourceFile[]
  refreshTokens RefreshToken[]
}

model TransactionType {
  id     String  @id @default(cuid())
  name   String  @unique
  hidden Boolean @default(false)

  classes TransactionClass[]
}

model TransactionGroup {
  id   String @id @default(cuid())
  name String @unique

  classes TransactionClass[]
}

model TransactionClass {
  id      String @id @default(cuid())
  name    String @unique
  groupId String
  typeId  String

  group        TransactionGroup @relation(fields: [groupId], references: [id])
  type         TransactionType  @relation(fields: [typeId], references: [id])
  classifiers  ClassifierRule[]
  transactions Transaction[]
}

model ClassifierRule {
  id       String   @id @default(cuid())
  classId  String
  regex    String
  value    Decimal? @db.Decimal(12, 2)
  valueMin Decimal? @db.Decimal(12, 2)
  valueMax Decimal? @db.Decimal(12, 2)
  date     String?  // YYYY-MM-DD exact date constraint, optional

  class TransactionClass @relation(fields: [classId], references: [id], onDelete: Cascade)
}

model TransactionSource {
  id     String @id @default(cuid())
  name   String @unique
  type   String
  userId String

  user         User          @relation(fields: [userId], references: [id], onDelete: Cascade)
  transactions Transaction[]
}

model TransactionSourceFile {
  id        String   @id @default(cuid())
  name      String
  dataHash  String
  userId    String
  createdAt DateTime @default(now())

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([name, userId])
}

model Transaction {
  id          String   @id @default(cuid())
  date        DateTime @db.Date
  description String
  amount      Decimal  @db.Decimal(12, 2)
  classId     String?
  sourceId    String
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  class  TransactionClass? @relation(fields: [classId], references: [id])
  source TransactionSource @relation(fields: [sourceId], references: [id])
}

model RefreshToken {
  id        String   @id @default(cuid())
  userId    String
  tokenHash String   @unique
  expiresAt DateTime
  createdAt DateTime @default(now())

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)
}
```

---

## 7. API Design

### REST `/api/v1` (mobile + external)

```
POST   /auth/token              # login → access + refresh token pair
POST   /auth/logout
POST   /auth/refresh

GET    /me

GET    /transactions?start=&end=&t_type=&t_group=&t_class=&value_gt=&value_lt=&cursor=&limit=
GET    /transactions/summary?period=&group_period=&t_type=&t_group=&t_class=&start_date=&end_date=&group_by=
GET    /transactions/total?period=&t_type=

GET    /groups?t_type=
GET    /classes?t_type=&t_group=

GET    /classifiers?classId=
POST   /classifiers
PATCH  /classifiers/:id
DELETE /classifiers/:id

GET    /sources
POST   /sources

POST   /imports                 # upload CSV file; returns import summary
GET    /imports/:sourceFileId   # status + row count for a prior import

POST   /internal/reclassify     # cron-triggered, shared secret auth
```

### Query Parameters — `GET /transactions/summary`

| Param | Values | Default |
|---|---|---|
| `period` | `3 Months`, `6 Months`, `12 Months`, `24 Months`, `All` | `12 Months` |
| `group_period` | `month`, `week`, `year` | `month` |
| `t_type` | `Debit Normal`, `Credit Normal`, `Debit Abnormal`, `Credit Abnormal` | `Debit Normal` |
| `group_by` | `group`, `class` | `group` |

### Principles

- Cursor-based pagination on all list endpoints (no offset)
- Zod DTOs are the single source of truth — OpenAPI is generated from them, not hand-written
- Never expose raw Prisma model shapes in responses
- All amounts returned as strings (avoid JSON float precision loss)

---

## 8. Authentication

- **Access token:** JWT, 15 minute expiry, signed with `ACCESS_TOKEN_SECRET`
- **Refresh token:** JWT, 30 day expiry, stored in `HttpOnly; Secure; SameSite=Strict` cookie
- **Rotation:** refresh endpoint issues new access + refresh token pair, invalidates old refresh token (stored hash in DB for single-use enforcement)
- **Mobile:** mobile clients receive refresh token in response body — flag via `?client=mobile` on the login endpoint

Refresh token revocation table (`RefreshToken`) lives in PostgreSQL.

---

## 9. Environment Configuration

All config via environment variables. `.env.example` is committed and kept up to date.

```env
# Database
DATABASE_URL=postgresql://user:password@db:5432/finance
POSTGRES_USER=finance
POSTGRES_PASSWORD=changeme
POSTGRES_DB=finance

# Auth
ACCESS_TOKEN_SECRET=
REFRESH_TOKEN_SECRET=

# App
NEXT_PUBLIC_APP_URL=http://localhost:3000
NODE_ENV=development

# Internal jobs
INTERNAL_JOB_SECRET=

# Storage (attachments)
ATTACHMENT_STORAGE_PATH=/data/attachments
```

Production secrets are never committed. Managed via `.env.production` on the VM, excluded from git.

---

## 10. Docker Compose

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: docker/app.Dockerfile
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
    env_file: .env
    ports:
      - "3000:3000"
    volumes:
      - attachments_data:/data/attachments
    command: >
      sh -c "npx prisma migrate deploy && npx prisma db seed && node server.js"

volumes:
  postgres_data:
  attachments_data:
```

**Startup sequence:**
1. `db` starts and passes healthcheck
2. `app` runs `prisma migrate deploy`
3. `app` runs `prisma db seed` (idempotent — seeds types, groups, classes from JSON config)
4. Next.js server starts

---

## 11. Background Jobs

### Phase 1 — Synchronous (no extra container)

- CSV imports run synchronously in the request (acceptable for files up to ~10k rows)
- Classification runs synchronously after each import
- Periodic re-classification triggered by host cron hitting `POST /api/v1/internal/reclassify` with shared secret header
- No worker container required

### Phase 2 — Worker Container (add when needed)

```yaml
  worker:
    build: ...
    command: node worker.js
    depends_on: [db]
```

The service layer is already transport-agnostic — the worker calls the same services the API does.

---

## 12. Backup Strategy

```bash
# /etc/cron.d/finance-backup — runs at 2am daily
0 2 * * * docker exec finance_db pg_dump -U $POSTGRES_USER $POSTGRES_DB \
  | gzip > /backups/finance_$(date +\%Y\%m\%d).sql.gz

# Retain 30 days
find /backups -name "*.sql.gz" -mtime +30 -delete
```

- Backups written to `/backups` on the host
- Restore command: `gunzip -c backup.sql.gz | docker exec -i finance_db psql -U $POSTGRES_USER $POSTGRES_DB`
- Restore script committed at `scripts/restore.sh`
- Restore tested monthly

---

## 13. Agentic Coding Guidelines

**Agents working on this codebase must:**

- Read `prisma/schema.prisma` before writing any data access code
- Read `src/dtos/` before writing any API handler
- Read `data/general/*.json` to understand seed data shape before touching classification logic
- Write domain logic first, then wire into services, then expose via router
- Never import Prisma client outside of `src/repositories/`
- Never put business logic in route handlers or tRPC routers
- Run `prisma migrate dev --name <description>` after any schema change
- Update the relevant DTO and regenerate OpenAPI after any API contract change
- Amounts are always `Decimal` — never `number` for money
- Classification logic lives in `src/domain/classification.ts` — regex engine and LRU cache are pure functions with no I/O
- CSV parsing uses `csv-parse`; always validate minimum 3 columns per row before processing
- Source name is extracted from filename as the substring before the first `_`; validate this before accepting an upload
- Import amounts arrive as float strings and must be rounded to 2dp before DB insertion; never store raw floats

**Commit order for a new feature:**

1. Schema change + migration
2. Repository method
3. Domain logic
4. Service method
5. DTO
6. Router / API handler
7. UI component

---

## 14. Future Evolution Path

| Step | Change | Impact |
|---|---|---|
| Mobile app | Generate typed client from OpenAPI spec | No backend changes |
| Import worker | Move `importService` to worker container | Same code, new entrypoint |
| Python analytics | Add sidecar container on internal Docker network | No app changes |
| Caching | Add Redis container, wrap repository calls | No domain logic changes |
| Nginx reverse proxy | Add container pointing to `app:3000` | No app changes |
| DB-editable classifiers | `ClassifierRule` already in schema; add CRUD UI | No schema changes |

---

## 15. Why This Architecture

| Principle | How it's met |
|---|---|
| 2 containers in Phase 1 | `app` + `db` only |
| Type-safe UI development | tRPC eliminates DTO boilerplate for browser calls |
| Stable mobile API | REST layer with versioning and OpenAPI docs |
| Full auditability | `TransactionSourceFile` hash history; re-import safe |
| Agentic-friendly | Strict layer boundaries, schema-first, single ORM |
| Extraction-ready | Service layer is transport-agnostic, no rewrites needed |
| Classification correctness | `ClassifierRule` in DB; seeded from JSON; two-pass matching with LRU cache |
