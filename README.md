# ClassNest

ClassNest is an internal Telegram tool for educators to build structured, printable activity packs for preschool groups.

It helps teachers:
- Browse categorized activities, crafts, and logic puzzles
- Assemble custom lesson packs
- Reduce repetition via anti-repeat tracking
- Export clean A4 PDFs for printing
- Manage content and rules through a simple local admin panel

Built for real classroom workflow — not a marketplace platform.

## Quick Start

1. Copy `.env.example` to `.env` and set BOT_TOKEN
2. Run:
   ```
   docker compose up -d --build
   ```
3. Open admin panel:
   http://localhost:8080
   (default credentials: admin / admin)