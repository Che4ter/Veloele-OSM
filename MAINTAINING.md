# Maintaining Velöle

## Rebuild and test

Requirements: Java 17+, Python 3, an OsmAndMapCreator release unzipped into
`mapcreator/` (the harness uses its `lib/*.jar`), and the OsmAnd `.obf` maps
of the test regions in `maps/`. These folders and `results/` are git-ignored.

- `python3 -m unittest discover -s harness -p 'test_*.py'` runs all tests
  (tests needing the jars skip without them).
- `profile/veloele.xml` is edited by hand; the route tests are the safety
  net.
- `harness/run.sh <xml> <profile> <params|-> <hh|astar> <out.json> [routes]`
  runs the test routes (`harness/routes.txt`; extra sets `routes-ch.txt`,
  `routes-touring.txt`) against `maps/`.
- `harness/turns.py <out.json>...` compares turn counts and cycle-path share;
  `harness/surface_share.py <out.json>...` reports cobblestone, sett and easy
  gravel per route.
- `harness/brouter_compare.py` tests `veloele.brf` against BRouter 1.7.10
  (download the release and the `.rd5` segments from brouter.de first).

The phone uses OsmAnd's C++ router, the tests the Java one. Both read the
same XML, but small differences are possible.

## Velöle bundle

The bundle adds the Velöle map style, `profile/veloele.render.xml`, a
trimmed copy of CycloRoute.

`python3 harness/pack_osf.py` builds and checks `dist/veloele.osf`
(`harness/check_osf.py <file.osf> [--sources .]` checks any bundle). Bundle
settings live in `profile/osf/*.json` and are edited directly. Opening the
file in OsmAnd adds the profile **Velöle** (contents: see the README).

Installing on the phone: see the README.

## Release

Push a tag, e.g. `git tag v1.0 && git push origin v1.0`. The *Release*
workflow (`.github/workflows/release.yml`) runs the tests, builds the bundle
and publishes a GitHub release with `veloele.osf`, `veloele.xml`,
`veloele.brf` and `veloele.render.xml` as separate files. Each file gets a
label, and the release text from `.github/release-notes.md` explains which
one to download.
