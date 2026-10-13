import java.io.*;
import java.nio.file.*;
import java.util.*;

import net.osmand.binary.BinaryMapIndexReader;
import net.osmand.binary.BinaryMapRouteReaderAdapter.RouteTypeRule;
import net.osmand.binary.RouteDataObject;
import net.osmand.data.LatLon;
import net.osmand.router.*;
import net.osmand.router.RoutePlannerFrontEnd.RouteCalculationMode;
import net.osmand.router.RouteResultPreparation.RouteCalcResult;
import net.osmand.util.MapUtils;

/**
 * Runs OsmAnd's Java router on real OBF maps and classifies the result.
 *
 * usage: Harness <routing.xml> <profile> <params k=v,..|-> <hh|astar> <routes.txt> <out.json> <obf>...
 * routes.txt lines: name;lat,lon;lat,lon
 */
public class Harness {

	static final String[] CATS = {"cycleway", "shared_path", "lane", "fietsstraat", "quiet_street",
			"rural_road", "main_road", "footway", "track_path", "ferry", "other"};

	public static void main(String[] a) throws Exception {
		String xml = a[0], profile = a[1], params = a[2], mode = a[3];
		List<String> routes = Files.readAllLines(Paths.get(a[4]));
		String out = a[5];
		List<BinaryMapIndexReader> readers = new ArrayList<>();
		for (int i = 6; i < a.length; i++) {
			readers.add(new BinaryMapIndexReader(new RandomAccessFile(a[i], "r"), new File(a[i])));
		}
		RoutingConfiguration.Builder builder;
		try (InputStream is = new FileInputStream(xml)) {
			builder = RoutingConfiguration.parseFromInputStream(is);
		}
		Map<String, String> pm = new LinkedHashMap<>();
		if (!params.equals("-")) {
			for (String kv : params.split(",")) {
				String[] s = kv.split("=");
				pm.put(s[0], s.length > 1 ? s[1] : "true");
			}
		}
		StringBuilder json = new StringBuilder("[\n");
		boolean first = true;
		for (String line : routes) {
			line = line.trim();
			if (line.isEmpty() || line.startsWith("#")) continue;
			String[] p = line.split(";");
			LatLon s = ll(p[1]), e = ll(p[2]);
			RoutingConfiguration config = builder.build(profile,
					new RoutingConfiguration.RoutingMemoryLimits(3000, 3000), pm);
			RoutePlannerFrontEnd fe = new RoutePlannerFrontEnd();
			if (mode.equals("hh")) {
				fe.setDefaultHHRoutingConfig();
			} else {
				fe.disableHHRoutingConfig();
			}
			RoutingContext ctx = fe.buildRoutingContext(config, null,
					readers.toArray(new BinaryMapIndexReader[0]), RouteCalculationMode.NORMAL);
			long t0 = System.currentTimeMillis();
			RouteCalcResult res;
			PrintStream so = System.out;
			System.setOut(new PrintStream(OutputStream.nullOutputStream()));
			try {
				res = fe.searchRoute(ctx, s, e, null);
			} finally {
				System.setOut(so);
			}
			long ms = System.currentTimeMillis() - t0;
			if (!first) json.append(",\n");
			first = false;
			if (res == null || !res.isCorrect() || res.getList().isEmpty()) {
				String err = res == null ? "null" : res.getError();
				System.out.printf("%-28s ERROR %s%n", p[0], err);
				json.append(String.format("{\"name\":\"%s\",\"error\":\"%s\"}", p[0], esc(err)));
				continue;
			}
			Map<String, Double> byCat = new LinkedHashMap<>();
			for (String c : CATS) byCat.put(c, 0.0);
			double dist = 0, time = 0;
			StringBuilder segs = new StringBuilder();
			for (RouteSegmentResult r : res.getList()) {
				RouteDataObject o = r.getObject();
				Map<String, String> tags = tags(o);
				String cat = categorize(tags);
				double d = segDist(r);
				dist += d;
				time += r.getSegmentTime();
				byCat.merge(cat, d, Double::sum);
				if (segs.length() > 0) segs.append(",");
				segs.append("{\"c\":\"").append(cat).append("\",\"id\":").append(o.getId() >> 6)
						.append(",\"h\":\"").append(esc(tags.getOrDefault("highway", tags.getOrDefault("route", "?"))))
						.append("\",\"pr\":").append(String.format(Locale.ROOT, "%.2f", config.router.defineSpeedPriority(o, r.isForwardDirection())))
						.append(",\"sp\":").append(String.format(Locale.ROOT, "%.1f", config.router.defineRoutingSpeed(o, r.isForwardDirection()) * 3.6))
						.append(",\"t\":\"").append(esc(tagStr(tags))).append("\",\"p\":[");
				int st = r.getStartPointIndex(), en = r.getEndPointIndex();
				int step = st <= en ? 1 : -1;
				boolean f2 = true;
				for (int i = st; ; i += step) {
					if (!f2) segs.append(",");
					f2 = false;
					segs.append(String.format(Locale.ROOT, "[%.6f,%.6f]",
							MapUtils.get31LatitudeY(o.getPoint31YTile(i)), MapUtils.get31LongitudeX(o.getPoint31XTile(i))));
					if (i == en) break;
				}
				segs.append("]}");
			}
			StringBuilder sum = new StringBuilder();
			StringBuilder cj = new StringBuilder();
			for (Map.Entry<String, Double> en : byCat.entrySet()) {
				if (cj.length() > 0) cj.append(",");
				cj.append(String.format(Locale.ROOT, "\"%s\":%.0f", en.getKey(), en.getValue()));
				if (en.getValue() > 0.5) {
					sum.append(String.format(Locale.ROOT, " %s=%.0f%%", en.getKey(), 100 * en.getValue() / dist));
				}
			}
			System.out.printf(Locale.ROOT, "%-28s %6.2f km %5.0f min calc %5.1fs |%s%n", p[0], dist / 1000, time / 60,
					ms / 1000.0, sum);
			json.append(String.format(Locale.ROOT,
					"{\"name\":\"%s\",\"from\":[%s],\"to\":[%s],\"dist\":%.0f,\"time\":%.0f,\"calcMs\":%d,\"cats\":{%s},\"segs\":[%s]}",
					p[0], p[1], p[2], dist, time, ms, cj, segs));
		}
		json.append("\n]\n");
		Files.writeString(Paths.get(out), json.toString());
	}

	static double segDist(RouteSegmentResult r) {
		RouteDataObject o = r.getObject();
		int st = r.getStartPointIndex(), en = r.getEndPointIndex();
		int step = st <= en ? 1 : -1;
		double d = 0;
		for (int i = st; i != en; i += step) {
			d += MapUtils.squareRootDist31(o.getPoint31XTile(i), o.getPoint31YTile(i),
					o.getPoint31XTile(i + step), o.getPoint31YTile(i + step));
		}
		return d;
	}

	static Map<String, String> tags(RouteDataObject o) {
		Map<String, String> m = new HashMap<>();
		for (int t : o.getTypes()) {
			RouteTypeRule rule = o.region.quickGetEncodingRule(t);
			m.put(rule.getTag(), rule.getValue());
		}
		return m;
	}

	static String tagStr(Map<String, String> t) {
		StringBuilder b = new StringBuilder();
		for (String k : new TreeSet<>(t.keySet())) {
			if (k.startsWith("name") || k.startsWith("osmand_ele") || k.startsWith("ref")) continue;
			b.append(k).append('=').append(t.get(k)).append(' ');
		}
		return b.toString().trim();
	}

	static String categorize(Map<String, String> t) {
		String h = t.getOrDefault("highway", "");
		String bicycle = t.getOrDefault("bicycle", "");
		boolean bikeDesignated = bicycle.equals("designated") || bicycle.equals("official");
		if ("ferry".equals(t.get("route"))) return "ferry";
		if (h.equals("cycleway")) return "cycleway";
		if ((h.equals("path") || h.equals("footway") || h.equals("pedestrian") || h.equals("bridleway")) && bikeDesignated) {
			return "shared_path";
		}
		for (Map.Entry<String, String> en : t.entrySet()) {
			String k = en.getKey(), v = en.getValue();
			if ((k.equals("cycleway") || k.startsWith("cycleway:") || k.startsWith("osmand_cycleway"))
					&& (v.contains("lane") || v.contains("track") || v.equals("true") || v.contains("busway"))) {
				return "lane";
			}
		}
		if ("yes".equals(t.get("cyclestreet")) || "yes".equals(t.get("bicycle_road"))) return "fietsstraat";
		switch (h) {
			case "residential": case "living_street": case "service": return "quiet_street";
			case "unclassified": case "road": return "rural_road";
			case "tertiary": case "tertiary_link": case "secondary": case "secondary_link": case "primary":
			case "primary_link": case "trunk": case "trunk_link": return "main_road";
			case "footway": case "pedestrian": case "steps": return "footway";
			case "track": case "path": case "bridleway": return "track_path";
		}
		return "other";
	}

	static LatLon ll(String s) {
		String[] p = s.split(",");
		return new LatLon(Double.parseDouble(p[0]), Double.parseDouble(p[1]));
	}

	static String esc(String s) {
		return s == null ? "" : s.replace("\\", "\\\\").replace("\"", "\\\"");
	}
}
