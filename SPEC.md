# Kids Pinterest Pack Builder — Technical Design & Specification (EN)

## 1. Objective
Build a Telegram bot for educators to:
- Browse a **card catalog** (Pinterest Pins or local library) through a **structured click UI** (inline keyboards; minimal typing).
- Add/remove/reorder cards inside a **Pack**.
- Export the Pack to **print-ready PDF** (A4 layouts).
- Reduce repetition via persisted **anti-repeat** signals:
  - Seen (browsing)
  - Hidden (never show again)
  - Exported (per group/class)

Also provide a **local admin panel** (simple web UI) to manage:
- Local content items (fallback library)
- Rule set (anti-repeat windows, default layout, UI page size)

## 2. MVP vs Later
### MVP (implemented scaffold)
- Telegram polling
- SQLite persistence + adapter layer for Postgres later
- Local content source (admin-managed)
- Pack builder + PDF export (card-based)
- Admin panel with Basic Auth (admin/admin by default)

### Later (planned)
- Pinterest OAuth + board/pin sync
- Worker queue for heavy exports
- Group profiles, richer filters, QR codes, answer keys

## 3. Key Entities
### Teacher (teacher_id)
For MVP use Telegram `chat_id`.

### Group/Class (group_id)
String label, stored in teacher settings (e.g. `stars_5yo`).

### ContentItem (Card)
Unified model used by all sources:
- item_id, source, category
- title, description
- image_ref (URL or local file path)
- source_url
- tags_json (free-form JSON)
- age_min/age_max, difficulty (optional)

### Pack
Ordered list of item_ids:
- pack_id, teacher_id, name
- pack_items: (position, item_id)

## 4. Modules
### 4.1 app/config.py
Loads env variables into a validated Settings model.

### 4.2 app/db/*
Repository contracts (interfaces) + factory:
- TeacherRepo (settings + active pack)
- ContentRepo (CRUD local items)
- PackRepo (ordered pack operations)
- AntiRepeatRepo (seen/hidden/exported)
- RulesRepo (JSON rule set)

SQLite implementation in `app/db/sqlite/*`.
Postgres adapter is reserved in `app/db/postgres/*` (not implemented in MVP).

### 4.3 app/domain/*
- selection.py: rule-based “next item” selector for local browsing
- packs.py: ensure active pack, pack helpers

### 4.4 app/export/pdf_renderer.py
Generates PDF using ReportLab:
- A4_2x2, A4_2x3, A4_1col layouts
- Each card: title + image + optional source URL
- Uses disk cache for remote images (URL → file)

### 4.5 app/ui/*
Aiogram routers and screens:
- Menu (Main / Local / Pack / Settings)
- Browse (local categories; card viewer; Next/Prev/Add/Hide)
- Pack (list, clear, export)
- Settings (group cycling, layout cycling)

### 4.6 app/admin/*
FastAPI admin panel on port 8080:
- Dashboard
- Content CRUD (incl. image upload stored in CACHE_DIR/uploads)
- Rules editor (JSON)

## 5. Rule Set (editable)
Stored as JSON in DB:
- default_layout: a4_2x2|a4_2x3|a4_1col
- seen_window: int
- exported_window: int
- page_size: int
- pdf_footer_show_source: bool

## 6. Contracts & Invariants
- Business logic uses repository contracts only.
- Switching SQLite → Postgres must not change domain or UI code.
- Export must not crash if an image download fails; render placeholder.

## 7. Risks (weakest link)
- Pinterest API access (external). MVP should ship with local library first.
- Image stability: require disk cache to avoid broken exports.
- SQLite write contention: acceptable for MVP; migrate to Postgres for scale.
