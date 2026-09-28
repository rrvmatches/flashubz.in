# FLASHUBZ MUSIC WORLD

## Original problem statement
Build a premium cinematic futuristic interactive 3D music universe named **FLASHUBZ MUSIC WORLD**, based on the uploaded FLASHUBZ landing-page artwork. Preserve FLASHUBZ branding and BLACK / DEEP RED / CHROME / SILVER / WHITE identity; never add a crown or generic rebranding. Landing must prominently display FLASHUBZ + MUSIC WORLD + a large red glass/chrome play orb + real audio waves + a compact DISCOVER OUR PAGES button. Main journey: landing → Discover → one individual song per 3D folder → song detail → real persistent playback with audio-reactive effects → authorized download / favorite / share. Do not use category folders or a standard flat streaming grid. Admin uploads must automatically produce new database-driven song folders without frontend code changes.

The supplied master prompt specifies: cinematic entrance, subtle mouse parallax, orb floating and orbiting rings, particles and music notes, Web Audio analysis for bass/mid/high reactions, 3D folder hover/open/scroll entrance, searchable Discover, persistent player (artwork/name/artist/previous/play-pause/next/progress/duration/volume/shuffle/repeat/download/favorite/waveform), song metadata pages with lyrics/LRC, related songs and same artist, browser libraries or accounts, contact form and exact configurable TikTok URL, secure admin dashboard, audio/cover/lyrics/metadata upload with publishing and distribution toggles, MongoDB-backed records, secure media storage/download links, analytics, SEO, responsive performance, mobile touch, reduced motion, accessible HTML alternatives, and scalable catalog loading. Routes: `/`, `/discover`, `/song/:slug`, `/playlist/:id`, `/favorites`, `/contact`, `/admin`.

## Explicit user choices
- “My own music files, which I’ll provide” — do NOT seed sample songs or invent artist names/releases. User has not yet provided audio or cover art.
- “Visitor library saved on this browser, with a separate secure admin login.” No listener sign-up/password accounts.
- Uploaded artwork URL: https://customer-assets-39nsmqrw.emergentagent.net/job_a4ba6b54-000b-4893-a4e4-f3d9194dca50/artifacts/orpqlu55_ad9043b1-999c-4efd-810e-7dbcba432ad5.png
- No exact TikTok URL yet. Keep unconfigured; never invent one.

## Personas
1. Listener: discovers songs, listens continuously across routes, saves browser favorites/playlists, reads lyrics, downloads authorized music, shares links.
2. FLASHUBZ owner/admin: uploads owned/licensed music, publishes/unpublishes/edits/deletes releases, manages editorial lists and social setting, monitors play/download/favorite counts, receives contact messages.

## Architecture decisions
- React 19 / React Router, Shadcn primitives, custom branded CSS with Manrope + Barlow Condensed, lucide icons; lazy song/contact/admin and Three.js chunks.
- Three.js 0.186.1 WebGL hero with geometries/materials/environment reflection, orbit rings, note sprites, particle layer, bloom, black floor/ripple rings. Actual original artwork crop is the branding asset; not AI-generated replacement branding. 3D CSS transform folder objects with hinged fronts and emerging covers.
- Central MusicProvider with one HTML audio element; Web Audio analyser uses actual currently playing audio. Real frequency buffers drive canvas waveforms and orb/light/ripple response. Only user gesture starts audio.
- Browser localStorage: visitor UUID, favorites IDs, playlists and song IDs, volume. Playlist audio loads in 48-ID batches. Discover server pagination (12 per page, max48/request), lazy covers, no audio preloading until selected.
- FastAPI at supervisor port8001, React3000. Frontend uses protected REACT_APP_BACKEND_URL; DB uses existing MONGO_URL. Mongo documents queried without `_id`; song responses use Pydantic schemas. Primary collections: songs, files, artists, albums, favorites (aggregate activity), playlists (admin editorial), events, downloads, messages, site_settings. Visitor account and playlist_songs collections are intentionally replaced by selected browser storage and playlist song-ID arrays.
- Managed object storage, service credentials server-only. Canonical storage paths stored in Mongo files; soft deletion. Audio proxied through checked backend media endpoint with HTTP Range support. Short-lived signed authorized download endpoint revalidates publication and permission. Cover optimization to max1200px WEBP. Audio validation via mutagen, max100MB; cover max10MB.
- `/tmp/flashubz-media-cache` is deliberately disposable, bounded to ~512MB. Source media remains in cloud object storage; no user file depends on /tmp persistence. Persistent app code, assets, tests, docs under `/app`.
- Admin credentials in backend environment (see memory/test_credentials.md), JWT HttpOnly/Secure session. Server requests SameSite=Strict; preview ingress can rewrite to SameSite=None;Partitioned. **Session-bound CSRF tokens required for all protected writes**, returned by login/me and sent as X-CSRF-Token. Independent of proxy Origin rewriting and cookie SameSite policy. Login attempt throttling.
- Contact delivers to database admin inbox, not external email. No external email integration was requested. TikTok profile set through admin settings with HTTPS/tiktok-domain validation.

## Implemented — 2026-09-28
- Full branded responsive public experience, original FLASHUBZ logo, animated Three.js hero and compact CTA; empty state honors missing owner music.
- Discover, 3D song folders/opening transitions, search across all five fields, sort, pagination.
- Persistent actual audio player, audio analysis/waveforms, metadata/LRC lyrics, related/artist tabs, authorized downloads and sharing.
- Browser favorites and full visitor playlist creation, rename/delete, add/remove, play and refresh persistence.
- Contact form validation, stored inbox, configurable exact TikTok link with new-tab behavior.
- Secure admin login/logout; dashboard/live counters/chart; actual cloud uploads; auto-folder; publishing/edit/delete; artists and visitor counts; downloads; editorial playlist management; settings.
- SEO page titles, descriptions, client-updated Open Graph and canonical links; `/api/sitemap.xml`, robots policy.
- Desktop1920x800/mobile390x844 screenshots, production build passed; initial E2E public flows/media/backend passed. Temporary ORIGINAL test-tone fixtures used then removed; real catalog remains empty.
- Initial testing caught browser admin Origin rejection; replaced brittle Origin comparison with session-bound CSRF; regression updated to account for preview cookie partitioning and fixed incorrect case assertion. Verified in final iteration 2 below.
- Final iteration 2 passed: admin real upload/edit/publish/unpublish/delete, settings, editorial lists, inbox/dashboard; browser favorites/playlists/persistent player; backend CSRF isolation and token restoration; desktop1920x800/mobile390x844 WebGL pixel and motion checks, no overflow. Reports: `/app/test_reports/iteration_2.json`. Backend initial suite9/9; additional CSRF7/7 and cleanup2/2. All TEST_ONLY data removed, public songs0 and TikTok empty.
- Post-test polish: chart initial dimensions prevent the transient -1 size warning; moved orb face/play/pause geometry in front of its curved core so icons are not partially occluded.
- Final direct screenshots at1920x800 and390x844 verified the corrected solid play glyph, visible framed WebGL scene, admin chart on both viewports, zero horizontal-overflow offenders, zero chart-size warnings, and successful logout. Final public songs0 and TikTok blank confirmed through external API.

## Prioritized remaining work
### P0 — owner inputs
- Owner uploads own music and optional cover/lyrics via admin studio. No music content supplied yet, so public library correctly empty.
- Owner configures exact TikTok profile if desired.
### P1 — refinements, not blocked core flows
- Full 3D corridor with scroll-driven camera/light sweeps (current folders have CSS3D entrance and hover/open effects).
- True floor reflection render targets, volumetric lighting and depth of field, richer high-frequency light streaks; current scene uses efficient environment/material reflections, bloom, particles and bass ripple rings.
- Adaptive frame-rate quality tiers and WebGL context-loss recovery beyond current DPR/particle mobile limits and no-WebGL artwork fallback.
- Search-optimized catalog indexes/external search and paginated admin inventory for libraries beyond several thousand songs; public catalog is already paginated.
- Server-rendered song social preview tags for crawlers without JavaScript (current song tags updated client-side).
### P2
- Optional editorial playlist publication in public library (admin editorial management is implemented; visitor personal playlists are separate/local).
- Optional email notifications for owner inbox, only if requested.

## Next actions
1. Deliver app link and initial owner admin access.
2. Owner uploads first music release and optional art/lyrics in `/admin/upload`.
3. Owner configures exact TikTok URL in `/admin/settings`.
4. Optional next phase: richer scroll-through 3D corridor and server-rendered song social previews.