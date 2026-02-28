# UI Design — Quantumizer (New Build)

**Generated:** 2026-02-28

---

## 1. Design Direction

The new build keeps all existing reports and interactions but replaces the Jinja2/Bootstrap/D3/jQuery stack with a modern React dashboard.

**Design goals:**
- **Dense but readable** — data-first, no decorative whitespace. Information per pixel is high.
- **Dark-first** — dark palette is the default; light mode is available but secondary.
- **Interaction parity** — every chart tooltip, breakdown modal, drilldown click, and copy button from the source system is preserved.
- **Uplift** — KPI cards, URL-persistent state, skeleton loaders, shareable links, and a sidebar layout modernise the experience without changing the workflows users know.

---

## 2. Technology Choices

| Concern | Choice | Rationale |
|---|---|---|
| UI framework | Next.js 14+ App Router | Matches architecture plan |
| Component library | **shadcn/ui** + Tailwind CSS | Headless, composable; dark mode via CSS variables |
| Charts | **Recharts** | React-native; `ComposedChart` handles stacked bars + line overlay on one axis; custom tooltips + `onClick` |
| Data grid | **AG Grid Community** (React) | Already proven in source project; Quartz dark theme; client-side sort/filter/copy |
| Dark mode | `next-themes` + Tailwind `dark:` | CSS-variable tokens; respects OS preference, persists in `localStorage` |
| Icons | `lucide-react` | shadcn default; consistent stroke weight |
| Font | **Inter** (body) + **JetBrains Mono** (amounts/IDs) | Inter replaces Noto Sans for sharper readability; mono for financial figures |
| URL state | `nuqs` (Next.js URL search params) | Period, filters, active group etc. live in the URL — links are shareable |

### Chart library note

Recharts `<ComposedChart>` covers all existing chart types:
- `<Bar stackId="a">` per group/class → stacked bar
- `<Line>` on the same chart → 3-month SMA overlay
- `<ReferenceLine y={0}>` → zero line on difference chart
- `<Tooltip content={<CustomTooltip />}>` → breakdown table inside tooltip
- `onClick` prop on `<Bar>` → breakdown modal

D3 is **not** used in the new build. Colour utilities (hash → HSL) are pure TypeScript functions.

---

## 3. Global Layout — Sidebar

Replace the top-only navbar with a **collapsible sidebar + top bar** pattern. This is more appropriate for a data dashboard with multiple views.

```
┌──────┬─────────────────────────────────────────────────┐
│      │ [≡]  Quantumizer          [🌙/☀]  [User ▾]     │  ← Top bar
│  S   ├─────────────────────────────────────────────────┤
│  I   │                                                  │
│  D   │  <page content>                                  │
│  E   │                                                  │
│  B   │                                                  │
│  A   │                                                  │
│  R   │                                                  │
│      │                                                  │
└──────┴─────────────────────────────────────────────────┘
```

**Sidebar items (icons + labels):**
```
🏠  Home
📊  Summary
⚖️  Compare
📋  Transactions
⬆️  Import
⚙️  Classifiers
🔌  Sources
────
⎋   Logout
```

**Sidebar states:**
- **Expanded** (default, ≥1280px): icon + label, 220px wide
- **Collapsed** (user toggle or <1280px): icon only, 56px wide; hover shows tooltip label
- **Mobile** (<768px): hidden by default, full-screen overlay on hamburger tap
- State persisted in `localStorage`

**Top bar:**
- Hamburger toggle (collapses/expands sidebar)
- App name / current page breadcrumb
- Dark/light mode toggle
- User display name + logout dropdown

---

## 4. Design Tokens (Dark Theme Defaults)

```
Background:    #0d1117   (page)
Surface:       #161b22   (cards)
Surface-2:     #21262d   (table headers, inputs)
Border:        #30363d
Text-primary:  #e6edf3
Text-muted:    #8b949e

Accent-blue:   #388bfd   (interactive, focus rings)
Surplus green: #3fb950   (positive delta)
Deficit red:   #f85149   (negative delta)
Warn amber:    #d29922

Chart palette: deterministic HSL from group/class name hash
SMA line:      #e6edf3 (white), dashed
```

These map to shadcn/ui CSS variables (`--background`, `--card`, `--muted`, etc.) so all shadcn components adapt automatically.

---

## 5. Pages

### 5.1 Home — Dashboard (`/`)

**Uplift from source:** Add KPI summary cards at the top. Shared Y-axis between Spend and Income charts. Surplus badge upgraded to a card.

**Layout:**

```
┌──────────────────────────────────────────────────────────────┐
│  [6M] [12M] [24M] [36M] [48M] [All]          ← period toggle │
├───────────┬──────────────┬──────────────┬────────────────────┤
│ This Month│ Rolling Avg  │ YTD Spend    │ Surplus / Deficit  │
│ Spend     │ (period)     │              │ (period total)     │
│ $4,201    │ $3,890 /mo   │ $28,450      │ +$1,234  ▲        │
│ ▲ 12% MoM │              │              │ Surplus            │
└───────────┴──────────────┴──────────────┴────────────────────┘

┌──────────────────────────────┬───────────────────────────────┐
│ Spend                        │ Income                        │
│ [Debit Normal ▾] [ALL ▾]    │ [Credit Normal ▾] [ALL ▾]    │
│ Total: $46,678  Avg: $3,889  │ Total: $53,210  Avg: $4,434  │
│                              │                               │
│  ████ ████ ████ ████ ████ ~~│  ████ ████ ████ ████ ████ ~~ │  ← stacked bar + SMA
│  J    F    M    A    M      │  J    F    M    A    M       │
└──────────────────────────────┴───────────────────────────────┘

┌──────────────────────────────┐
│ Surplus / Deficit            │  ← signed bar chart
│ Avg: +$544                   │
│  ▓▓▒▒ ▓▓▒▒ ─── ▓▓▒▒         │
│  +800 +640  -120  +890       │
└──────────────────────────────┘
```

**KPI Cards:**
- **This Month Spend** — current calendar month total for selected type. MoM % change badge (green = less spend, red = more spend).
- **Rolling Average** — average monthly total over the selected period.
- **YTD Spend** — year-to-date total.
- **Surplus / Deficit** — sum of (Income − Spend) over the period. `+` = green, `−` = red. Label: "Surplus" or "Deficit".

KPI cards update when the period toggle changes.

**Chart interactions (carry over exactly):**
- Hover bar segment → floating tooltip: breakdown table (Area | Amount | Pct), value-sorted, highlighted row = hovered segment
- Click bar segment → `<BreakdownModal>` with alphabetically sorted table + total badge + Copy TSV
- 3-month SMA line: white dashed, starts at month 3
- Shared Y-axis max between Spend and Income (state lifted to Home page component)
- Resize → charts redraw (Recharts handles this via `<ResponsiveContainer>`)

---

### 5.2 Summary — Drilldown Tables (`/summary`)

**Uplift from source:** URL-persistent state. Filter breadcrumb shows active context clearly. Transaction detail panel as a right-side **drawer** (Sheet) instead of a centred modal — keeps the grid visible.

**Layout:**

```
[Period ▾] [Type ▾]

┌──────────────┬────────────────────────┬──────────────┐
│ Group Total  │ Group By Month         │ Class Total  │
│ 400px        │ 400px                  │ 400px        │
│ (AG Grid)    │ (AG Grid)              │ (AG Grid)    │
│ ► clickable  │ ► clickable            │ ► clickable  │
└──────────────┴────────────────────────┴──────────────┘

┌──────────────────────────────────────────────────────┐
│ Transactions  [Food - 2024-03 - Bakery]  [🔍___] [⎘]│
│ (AG Grid, viewport-height adaptive)                  │
└──────────────────────────────────────────────────────┘

                                     ┌────────────────────┐
                                     │ Transaction detail  │  ← right drawer (Sheet)
                                     │ ID: 1234           │
                                     │ Date: 2024-03-15   │
                                     │ Description: COLES │
                                     │ Amount: $87        │
                                     │ Class: Supermarket │
                                     │ Group: Food        │
                                     │ Source: ANZ        │
                                     │ Type: Debit Normal │
                                     │ ─────────────────  │
                                     │ Classifier snippet │
                                     │ { "regex": ".*..." }│
                                     │ [Copy JSON]        │
                                     │ [Google Search]    │
                                     │ [+ Add Classifier] │
                                     └────────────────────┘
```

**Drilldown interaction (identical to source):**
1. Click Group Total row → clears Class and Transaction grids; loads Group By Month for that group; loads all Transactions for that group
2. Click Group By Month row → loads Class Total (group × month); loads Transactions (group × month)
3. Click Class Total row → loads Transactions (group × month × class)
4. Click Transaction row → opens right drawer with transaction detail

**URL state:** `?period=12+Months&type=Debit+Normal&group=Food&month=2024-03&class=Bakery` — paste the URL and the drilldown context is restored.

**Transaction detail drawer (uplift):**
- Replaces the centred modal with a right-side `<Sheet>` (shadcn) — the grid stays visible and interactive
- Auto-generated JSON snippet uses the transaction description (escaped for regex)
- **[+ Add Classifier]** button → opens `<ClassifierRuleForm>` inside the same drawer (pushed as a second panel), pre-filled with the generated regex and the transaction's current class

---

### 5.3 Compare — Multi-Panel (`/compare`)

**Uplift from source:** Panel count is configurable (1–4). Add/remove panels dynamically. Each panel is a card that can be independently pinned.

**Layout:**

```
[3M] [6M] [12M] [24M]    [+ Add Panel]    (max 4)

┌───────────────────────────────────┐  ┌──────────────────────────────────┐
│ Panel 1                    [✕]   │  │ Panel 2                   [✕]   │
│ [Type ▾] [Group ▾] [Class ▾]     │  │ [Type ▾] [Group ▾] [Class ▾]    │
│ Avg: $1,234                      │  │ Avg: $987                       │

│ Stacked bar (150px)              │  │ Stacked bar (150px)             │
└───────────────────────────────────┘  └──────────────────────────────────┘
┌───────────────────────────────────┐  ┌──────────────────────────────────┐
│ Panel 3                    [✕]   │  │ Panel 4                   [✕]   │
│ ...                              │  │ ...                             │
└───────────────────────────────────┘  └──────────────────────────────────┘
```

**Panels:** 2-column grid on desktop; 1-column on tablet/mobile. Each panel is independently scrollable if taller than viewport.

**Period toggle** shared — updates all panels simultaneously.

**[+ Add Panel]** adds a new card with default type = Debit Normal. [✕] removes a panel. Minimum 1 panel. Panel config persisted in `localStorage` (type, group, class selection per panel).

---

### 5.4 Transactions — Raw Search (`/transactions`)

**Uplift from source:** Filter chips instead of dropdowns. Amount range as a slider. Description search is always visible (not inside the grid header).

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│ Filter:                                                    │
│ [Debit Normal ×] [12 Months ×] [< $500 ×]  [Clear all]   │  ← filter chips
│                                                            │
│ 🔍 [Description contains...________________]              │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ 1,247 transactions                                [⎘ Copy] │
│ AG Grid: Date ↓ | Description | Amount | Class | Group    │
│          | Source | Type                                   │
└────────────────────────────────────────────────────────────┘
```

**Filter chips:** each active filter shown as a dismissable chip. Clicking a chip opens a popover to change that filter's value.

**Filter bar options:**
- Transaction type (single select: 4 types)
- Period (single select: 1M / 3M / 6M / 12M / 24M / All) OR custom date range picker (start / end)
- Amount Less Than (select or text input)
- Amount Greater Than (select or text input)
- Description (live text search, client-side AG Grid filter)

**Row count badge** shows how many transactions are loaded (before client-side filter) and how many match after filter.

**Clicking a row** → same right-side `<Sheet>` drawer as Summary page.

**URL state:** all filters in URL params for shareable links.

---

### 5.5 Import — CSV Upload (`/import`)

**Uplift from source:** This is a new page. Drag-and-drop, real-time validation, result summary, and import history.

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│ Upload CSV                                                 │
│                                                            │
│  ┌──────────────────────────────────────────────────┐     │
│  │                                                  │     │
│  │         ⬆  Drag & drop or click to browse        │     │
│  │                                                  │     │
│  │  Filename format: {source}_{YYYY-MM}.csv         │     │
│  │  Columns: date (DD/MM/YYYY), amount, description │     │
│  └──────────────────────────────────────────────────┘     │
│                                                            │
│  ✓ ANZ_2024-03.csv  (3 files queued)  [Upload All]        │
│  ✗ badfile.csv — filename format invalid                   │
└────────────────────────────────────────────────────────────┘

Result card (shown after upload):
┌────────────────────────────────────────────────────────────┐
│ ✓ Import complete — ANZ_2024-03.csv                        │
│                                                            │
│  Source:       ANZ (Cheque)                                │
│  Inserted:     47 transactions                             │
│  Skipped:      12 (duplicates)                             │
│  Classified from: 2024-03-01                               │
│                                                            │
│  [View Transactions →]                                     │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│ Import History                                             │
│ AG Grid: Filename | Source | Hash (short) | Date | Rows   │
└────────────────────────────────────────────────────────────┘
```

**Client-side validation before upload:**
- Filename must match `{something}_{YYYY-MM}.csv` — show inline error if not
- Multiple files can be queued; each validated independently
- Files with invalid names are highlighted red and excluded from upload

**Upload flow:**
- `POST /api/v1/imports` (multipart form)
- Progress indicator per file
- On success: result card with inserted/skipped counts and earliest classified date
- On duplicate file (same hash): yellow warning "Already imported — skipped"
- On partial failure: show rows that failed with error messages

**[View Transactions →]** button navigates to `/transactions` with the source filter pre-applied.

---

### 5.6 Classifiers — Rule Management (`/classifiers`)

**Uplift from source:** This is a new page. Replaces manual JSON file editing.

**Layout:**

```
[Group ▾] [Class ▾]  🔍 [Filter by regex...]   [+ Add Rule]  [▶ Reclassify All]

┌────────────────────────────────────────────────────────────┐
│ AG Grid: Class | Group | Regex | Constraints | Actions     │
│                                                            │
│ Supermarket  │ Food  │ .*COLES.*        │ —           │ ✏ 🗑│
│ Bakery       │ Food  │ .*BAKERY.*       │ —           │ ✏ 🗑│
│ Rent         │ Loans │ .*REAL ESTATE.*  │ value: 2450 │ ✏ 🗑│
└────────────────────────────────────────────────────────────┘
```

**Constraints column** shows a compact summary: `value: X`, `min: X max: Y`, `date: YYYY-MM-DD`, or `—`.

**`<ClassifierRuleForm>` modal (add/edit):**

```
┌──────────────────────────────────────────────────────────┐
│ Add / Edit Classifier Rule                               │
│                                                          │
│ Class:     [Supermarket (Food)  ▾]                      │
│                                                          │
│ Regex:     [.*COLES.*_____________________________]      │
│            Tip: case-insensitive, matched against        │
│            description.toUpperCase()                     │
│                                                          │
│ Constraints (all optional):                              │
│ Value:     [_______]   (exact amount match)              │
│ Min:       [_______]   Max: [_______]   (amount range)   │
│ Date:      [YYYY-MM-DD]                                  │
│                                                          │
│ ─── Live regex tester ──────────────────────────────── │
│ Testing against last 100 transactions...                 │
│                                                          │
│ ✓ 2024-03-15  COLES SUPERMARKET GEELONG  $87.30  match  │
│ ✓ 2024-02-28  COLES EXPRESS WAURN PONDS  $24.50  match  │
│ ✗ 2024-03-10  WOOLWORTHS HIGHTON        $112.00          │
│                                                          │
│                                    [Cancel]  [Save]      │
└──────────────────────────────────────────────────────────┘
```

**Live regex tester:**
- Debounced 400ms on regex input change
- Fetches last 100 transactions via `GET /api/v1/transactions?limit=100`
- Tests regex client-side against `description.toUpperCase()`
- Shows matches in green, non-matches in grey — no server round-trip for testing
- On constraint change (value/min/max), applies the full constraint logic client-side

**[▶ Reclassify All]:**
- `POST /api/v1/internal/reclassify`
- Shows spinner + "Reclassifying…" during the call
- On complete: toast notification "Reclassified N transactions"

**Add Classifier shortcut (from transaction detail drawer):**
- [+ Add Classifier] pre-fills the form: regex = `.*<escaped description>.*`, class = current transaction class
- Opens the form as a modal (not inline) so the drawer stays visible

---

### 5.7 Sources (`/sources`)

Lightweight management page. Not a primary workflow.

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│ Import Sources                                             │
│                                                            │
│ AG Grid: Name | Type | Transactions | Last Import Date     │
│                                                            │
│ ANZ      │ file │ 2,341 │ 2024-03-28                      │
│ CBA      │ file │  892  │ 2024-02-14                      │
└────────────────────────────────────────────────────────────┘
```

Clicking a source row links to `/transactions?source=<id>` pre-filtered.

---

## 6. Shared Components

| Component | Used on | Notes |
|---|---|---|
| `<KpiCard>` | Home | Title + value + MoM badge + delta arrow |
| `<PeriodToggle>` | Home, Compare | Radio group; period in URL param via `nuqs` |
| `<SpendChart>` | Home | Recharts ComposedChart: stacked Bar + Line (SMA); custom tooltip |
| `<DifferenceChart>` | Home | Recharts BarChart; signed bars with green/red fill |
| `<BreakdownModal>` | Home charts | shadcn Dialog; breakdown table + Copy TSV |
| `<TransactionSheet>` | Summary, Transactions | shadcn Sheet (right drawer); transaction detail + classifier snippet + Add Classifier action |
| `<ClassifierRuleForm>` | Classifiers, TransactionSheet | shadcn Dialog; regex form + live tester |
| `<AgGridDark>` | Summary, Transactions, Classifiers, Import, Sources | Wrapper: Quartz dark theme pre-configured; Noto Sans font |
| `<TypeSelect>` | Home, Summary, Compare, Transactions | shadcn Select; 4 type options |
| `<GroupSelect>` | Home, Compare | Async shadcn Select; fetches from `GET /api/v1/groups?t_type=` |
| `<ClassSelect>` | Compare, Classifiers | Async shadcn Select; cascades from GroupSelect |
| `<FilterChip>` | Transactions | Dismissable chip showing active filter; click to change |
| `<AmountBadge>` | KPI cards, modals | Green/red coloured amount display |
| `<CopyButton>` | All grids, modals | Copies TSV or JSON to clipboard; shows Copied/Failed state for 1.2s |

---

## 7. Interaction Patterns (carry over + modernised)

### Stacked Bar Chart (all chart pages)

| Interaction | Behaviour |
|---|---|
| Hover bar segment | Floating tooltip: breakdown table (Area \| Amount \| Pct), sorted by value desc, hovered segment highlighted |
| Click bar segment | `<BreakdownModal>`: alphabetical breakdown + total badge + Copy TSV |
| 3-month SMA line | White dashed; `defined` guard skips first 2 months; drawn on top of bars |
| Period change | All three Home charts re-fetch and redraw together |
| Window resize | `<ResponsiveContainer>` handles automatically |

### Summary Drilldown

| Interaction | Behaviour |
|---|---|
| Click Group Total row | Clears Class + Transaction grids; loads Group By Month + all Transactions for group |
| Click Group By Month row | Loads Class Total + Transactions for (group × month) |
| Click Class Total row | Loads Transactions for (group × month × class) |
| Click Transaction row | Opens right `<Sheet>` with transaction detail |
| URL | All drilldown context in URL; back button restores prior state |

### Classifier Shortcut Workflow

```
Transaction row click
  → Sheet opens (transaction detail)
  → [+ Add Classifier] click
  → ClassifierRuleForm opens (modal)
    → regex pre-filled from description
    → class pre-filled from transaction.class
    → live tester immediately shows matches
  → [Save] → POST /api/v1/classifiers
  → Toast: "Classifier saved. Run reclassify to apply."
  → [▶ Reclassify] button in toast or on Classifiers page
```

### Copy to Clipboard

All Copy buttons export TSV format:
- `navigator.clipboard.writeText` (primary)
- `textarea + execCommand('copy')` (fallback for non-secure context)
- Button label: `Copy` → `Copying…` → `Copied` / `Copy failed` (resets after 1.2s)

---

## 8. Colour Strategy

**Segment colours (charts):** Hash group/class name string → hue in HSL colour space. Saturation 60%, Lightness 55% (dark theme). Same name always produces the same colour — stable across page loads and filter changes.

```typescript
function nameToHsl(name: string): string {
  let hash = 0
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
  const hue = hash % 360
  return `hsl(${hue}, 60%, 55%)`
}
```

**Fixed colours:**

| Use | Token | Value |
|---|---|---|
| Surplus / positive | `--color-surplus` | `#3fb950` |
| Deficit / negative | `--color-deficit` | `#f85149` |
| SMA line | — | `#e6edf3` (near-white) |
| AG Grid row hover | — | `rgba(0,0,0,0.35)` |
| AG Grid selected text | — | `#ffff00` |
| MoM up (spend) | `--color-warn` | `#f85149` (more spend = bad) |
| MoM down (spend) | `--color-good` | `#3fb950` (less spend = good) |

---

## 9. New Reports

Not in the current system, but fit the data model and would add meaningful value:

| Report | Location | Description |
|---|---|---|
| **Unclassified queue** | Home KPI card + `/transactions?class=Undefined+Debit` | Count of Undefined Debit/Credit transactions with a "Fix now" link. Surfaces data quality instantly. |
| **Year-on-Year** | Home (optional chart) | Same months this year vs last year as a grouped bar chart. Toggle on/off. |
| **Top N transactions** | Summary sidebar / drawer | Largest individual transactions in the selected period. Good for spotting one-offs. |
| **Monthly trend card** | Home | Current month vs prior month % change with a sparkline. |
| **Classifier coverage** | Classifiers page | % classified vs unclassified over time, as a small area chart. Motivates classifier maintenance. |
| **Source contribution** | Summary | Donut chart: proportion of spend by `TransactionSource`. Useful for multi-bank users. |

---

## 10. Page → Route → tRPC Mapping

| Page | Route | Primary tRPC Procedures |
|---|---|---|
| Home | `/` | `transactions.summary`, `transactions.total` |
| Summary | `/summary` | `transactions.total`, `transactions.summary`, `transactions.search` |
| Compare | `/compare` | `transactions.summary`, `groups.list`, `classes.list` |
| Transactions | `/transactions` | `transactions.search` |
| Import | `/import` | `imports.upload`, `imports.list` |
| Classifiers | `/classifiers` | `classifiers.list`, `classifiers.create`, `classifiers.update`, `classifiers.delete`, `classifiers.reclassify` |
| Sources | `/sources` | `sources.list` |

---

## 11. Agentic UI Guidelines

**Agents building UI must:**

- Read this file and [finance-tracker-architecture.md](finance-tracker-architecture.md) before starting any page
- Use `<AgGridDark>` wrapper for all data tables — never plain `<table>` for grids
- Use Recharts `<ComposedChart>` for any chart needing both bars and a line
- Segment colours **must** use `nameToHsl()` — never hardcoded arrays or ordinal scales
- Shared Y-axis max on Home (Spend + Income) must be state lifted to the Home page component — both charts receive `yMax` as a prop
- `<TransactionSheet>` is a right-side sheet (not a centred modal) — always use it for transaction detail
- Period filter lives in the URL via `nuqs` — never in local component state only
- Amount display: `toLocaleString('en-AU', { maximumFractionDigits: 0 })` — no decimals, Australian locale
- All copy operations use `<CopyButton>` component — never inline clipboard code
- AG Grid: Quartz dark theme only; import `@ag-grid-community/react`; do not import legacy CSS theme files
- The classifier regex tester is **client-side only** — no API call needed for the regex match preview; only the initial transaction fetch is async
