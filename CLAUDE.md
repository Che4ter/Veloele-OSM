# Velöle – notes for Claude

OsmAnd setup for bicycle touring and travel: routing profile, navigation
settings, map style and POI filters, shipped as one `.osf` bundle, plus a
BRouter version of the routing. Public repo `Che4ter/Veloele-OSM`, GPL-3.0
only (not "or later"). User docs: `README.md`; build, test and release:
`MAINTAINING.md`.

## Principles

- Keep it simple: hand-edited, checked-in files plus tests, no generators.
  `profile/veloele.xml` and `profile/osf/*.json` are edited directly.
- Keep both engines in sync: every routing change goes into
  `profile/veloele.xml` (OsmAnd) and `profile/veloele.brf` (BRouter), with
  tests and route runs for both. Where one engine can't see a tag, say so in
  a comment and in the test docstring.
- Credit upstreams when touching derived files: OsmAnd-resources
  (`veloele.xml`, GPL-3.0), BRouter `gravel.brf` (`veloele.brf`, ideas
  only, MIT), CycloRoute by Louis, github.com/OsmAnd-Rendering/Cycling
  (`veloele.render.xml`, GPL-3.0).
- Docs and code comments are in English. The bundle's user-facing names
  (POI filters, quick actions, voice) are German on purpose.

## Layout

- `profile/veloele.xml` – OsmAnd routing; `profile/veloele.brf` – BRouter.
- `profile/veloele.render.xml` – map style (trimmed CycloRoute).
- `profile/osf/` – bundle contents: `items.json` (manifest),
  `profile_veloele.json` (app-profile settings), POI filters, quick actions.
- `harness/` – tests, bundle packer/checker, route comparison tools.
- Git-ignored, local only: `maps/`, `mapcreator/`, `results/`, `dist/`,
  `.superpowers/`, `docs/superpowers/`, `.serena/`.

## Commands

- Tests: `python3 -m unittest discover -s harness -p 'test_*.py'`
  (stdlib only). Run before every commit.
- Bundle: `python3 harness/pack_osf.py` → `dist/veloele.osf`, checked.
- Route runs need `mapcreator/` jars and `maps/*.obf`; see MAINTAINING.md.

## Git and releases

- Commits and tags are GPG-signed (already configured; pass `-S` anyway).
  Never add a `Co-Authored-By` line. Show the user the commit message
  before committing. Author `Che4ter <github@42.wtf>` is fine.
- Remote is SSH. The SSH and GPG keys live on a smartcard: every push and
  signature waits for the user to touch it, so run pushes in the
  background and tell the user to touch the card. "agent refused
  operation" means the card was not touched or is not inserted.
- Release: push a `v*` tag. `.github/workflows/release.yml` runs the tests,
  builds the bundle and publishes `veloele.osf`, `veloele.xml`,
  `veloele.brf` and `veloele.render.xml` as labelled assets, with
  `.github/release-notes.md` on top of generated notes. Keep the
  asset file names: OsmAnd needs `*.render.xml`, and the bundle refers to
  `veloele.xml/veloele`.
- CI has no `mapcreator/`: it downloads `poi_types.xml` from a pinned
  OsmAnd-resources commit into `mapcreator/poi_types.xml`, which
  `check_osf.load_poi_types` falls back to. Any new test that needs local
  data must skip without it, or CI breaks.
- Use the latest major versions of GitHub actions.

## OsmAnd learnings

- Settings source of truth: `OsmandSettings.java` in osmandapp/OsmAnd.
  Keys marked `makeProfile()` can go in `profile_veloele.json`; keys marked
  `makeGlobal()` apply to all profiles, so the bundle must not set them
  (user decision), e.g. the recorded track's `current_track_*`.
- Route line: `route_line_coloring_type: altitude` (free; only slope and
  attribute colouring need a paid plan). Without heights on the route
  OsmAnd silently draws the default line.
- Track colour and split markers are stored per track (GPX/track DB),
  not per profile; the bundle cannot set defaults for opened tracks.
- OsmAnd does not replace an existing style file on import; the old
  `rendering/veloele.render.xml` has to be deleted first. A hand-installed
  `routing/veloele.xml` makes the import report a conflict.
- On first import OsmAnd drops the bundle's map-style setting; the user
  selects *veloele* once.
- The fast route calculation uses precomputed data for the stock bicycle
  profile and is slow with veloele, so the bundle sets
  `route_calculation_method: STANDARD_ONLY`.
- The phone uses OsmAnd's C++ router, the harness the Java one; both read
  the same XML, but small differences are possible.
