# Velöle – OsmAnd for bicycle touring and travel

Velöle is a ready-made OsmAnd setup for touring and travelling by bike. One
bundle file, `veloele.osf`, adds an app profile **Velöle** with:

- **Routing** tuned for loaded touring bikes (see below).
- **Navigation** settings for riding: the route line shows the elevation
  profile, the screen shows next turns, distance, time, speed and an elevation
  chart, and German voice guidance is set up.
- **A map style** for cycling, based on CycloRoute: cycle and MTB routes,
  contour lines, access restrictions and cycling POIs; buildings, house
  numbers and admin borders are hidden.
- **POI filters** for what you need on tour: *Wasser* (drinking water,
  springs), *Übernachten* (campsites, huts, shelters) and *Essen unterwegs*
  (bakeries, supermarkets, cafés), plus a quick-action button to toggle them.

The routing is also available on its own for OsmAnd (`profile/veloele.xml`)
and BRouter (`profile/veloele.brf`).

## Install the bundle (Android)

1. Download `veloele.osf` from the
   [latest release](https://github.com/Che4ter/Veloele-OSM/releases/latest)
   on the phone.
2. Open the file with OsmAnd and import it.
3. Select *Configure map → Map style → veloele* once (OsmAnd drops the
   bundle's map style setting on the first import).
4. Enable the *Contour lines* plugin and download the region maps with their
   contour/terrain data; install German TTS voice data if asked.
5. Leave *Configure map → Hide POI icons* **on**; the style draws its own
   cycling POIs.

If `routing/veloele.xml` was installed by hand before, delete it first, or
the import reports a conflict.

**Updating:** OsmAnd does not replace an existing style file on import.
Delete `Android/data/net.osmand.plus/files/rendering/veloele.render.xml` (and
any `veloele_*.render.xml`) first, e.g. over USB from a PC, restart OsmAnd,
then import the new bundle.

## Routing

- Prefers cycle paths, bicycle streets, shared foot/cycle paths and signed
  cycle routes; avoids main roads without a cycle facility.
- National and international cycle routes keep a minimum priority even on
  main roads (secondary 0.6, primary 0.5), because often there is no
  alternative. Regional routes too, but only where the speed limit is
  50 km/h or less, e.g. through villages.
- Avoids footpaths and staircases: 10 m of steps cost about a 2.8 km detour.
- Cobblestones cost about 3×, sett about 2× as much as asphalt; compacted
  gravel and good tracks count as 15 km/h.
- Prefers routes with fewer turns; ETAs assume about 18 km/h; ferries are
  avoided by default.

The usual OsmAnd route parameters still work. **Avoid ferries** is on by
default. **Prefer unpaved roads** is a gravel mode: tracks and paths count as
good as cycle paths, ridden at 13–17 km/h.

**Long routes:** OsmAnd's fast mode ("Use fast route calculation") uses
precomputed data for the stock bicycle profile and recalculates the parts
where veloele's costs differ. Routes stay correct but can take long to
calculate, so the bundle sets *Route calculation method* to **Standard only**.

### Routing only, without the bundle

1. Copy `veloele.xml` (from the release or `profile/`) to
   `Android/data/net.osmand.plus/files/routing/` (`net.osmand` for the free
   version; create `routing` if missing).
2. Restart OsmAnd.
3. *Settings → App profiles → New profile*, based on *Cycling*.
4. In that profile: *Navigation settings → Navigation type* → **veloele**.

## Navigation

The bundle sets these for the Velöle profile only:

- **Route line** coloured by elevation. Without elevation data on the route,
  OsmAnd draws the normal route line instead. Works in the free version.
- **Screen:** next turn and the one after, street name and lanes at the top;
  distance, time to destination, speed, altitude and clock on the right;
  elevation chart at the bottom. Arrival time is shown.
- **Map:** rotates with the direction of travel, auto-zoom, volume buttons
  zoom, screen turns on for turn instructions, always day mode.
- **Voice:** German TTS with street names, recalculation, route deviation,
  GPS status and waypoint announcements; no speed limits, cameras or
  tunnels; music is not interrupted.
- **Recalculation** when off route or riding the wrong way stays on.

## BRouter (brouter-web)

Open [brouter-web](https://brouter.m11n.de) (or any other instance), then
*Customize profile*, paste `veloele.brf` (from the release or
`profile/`) and press *Upload*
(the upload is temporary; paste it again later). Options:

- **surface_mode**: avoid unpaved / neutral (default) / prefer gravel
- **hill_mode**: ignore / moderate (default; 1 m climb ≈ 80 m detour) / strong
- **allow_ferries** (default off)

Built in: turn penalty 15 s, traffic lights, stop signs, cycle barriers and
fords cost extra; roads with high maxspeed or estimated traffic are avoided
(ideas from BRouter's `gravel.brf`). A sidewalk where bicycles are allowed
(`sidewalk:right:bicycle=yes`, e.g. "Fussweg, Velo gestattet") counts like
a minor road; OsmAnd does not see this tag.

To ride a BRouter route in OsmAnd: export GPX with *OsmAnd* turn
instructions, open it in OsmAnd → *Follow track* with **Attach to roads**
off.

## Credits

- `veloele.xml` is built on OsmAnd's bicycle profile from
  [OsmAnd-resources](https://github.com/osmandapp/OsmAnd-resources).
- `veloele.brf` borrows ideas from BRouter's `gravel.brf`
  ([BRouter](https://github.com/abrensch/brouter)).
- `veloele.render.xml` is a trimmed copy of the CycloRoute map style by Louis
  ([OsmAnd-Rendering/Cycling](https://github.com/OsmAnd-Rendering/Cycling)).
- Map data © OpenStreetMap contributors.

Licence: GPL-3.0, see [LICENSE](LICENSE).

Building and testing: see [MAINTAINING.md](MAINTAINING.md).
