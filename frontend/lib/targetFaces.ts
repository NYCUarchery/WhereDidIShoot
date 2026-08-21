// Pure target-face geometry and scoring. No Vue imports, no API imports.
//
// Every geometric and scoring decision for the arrows page must be derived
// from a single TargetFaceConfig so the 6-ring (compound) and 10-ring
// (recurve) cutoffs can never drift apart.

export type TargetFaceType = "compound" | "recurve";

export type ScoreColorBand = "gold" | "red" | "blue" | "black" | "white" | "miss";

export interface TargetPoint {
  x: number;
  y: number;
}

export interface TargetRingBoundary {
  /** Radius at which the separator line is drawn. */
  readonly radius: number;
  /** Stroke colour for that line (light inside the black rings, dark elsewhere). */
  readonly stroke: string;
}

export interface TargetRing {
  readonly score: number;
  readonly outerRadius: number;
  readonly fill: string;
}

export interface TargetFaceConfig {
  readonly type: TargetFaceType;
  /** Human readable description used to build the SVG aria-label, e.g. "six-ring compound". */
  readonly descriptionLabel: string;
  /** Scoring rings, ascending by score (and therefore descending by radius). */
  readonly rings: readonly TargetRing[];
  /** Ring separator lines, one per ring, outer edge first. */
  readonly ringBoundaries: readonly TargetRingBoundary[];
  /** Beyond this radius (after arrow-radius/line-allowance shrink) the shot is a miss. */
  readonly scoringOuterRadius: number;
  /** Exactly two dashed guide-ring radii drawn outside the scoring rings. */
  readonly missGuideRadii: readonly [number, number];
  /** Furthest radius a plotted/dragged point may be clamped to. */
  readonly maxPlottedRadius: number;
}

// Shared geometry constants (identical for every face type).
export const RING_WIDTH_CM = 4;
export const ARROW_DIAMETER_CM = 0.558;
export const ARROW_RADIUS_CM = ARROW_DIAMETER_CM / 2;
export const RING_LINE_WIDTH_CM = 0.12;
export const RING_LINE_SCORING_ALLOWANCE_CM = RING_LINE_WIDTH_CM / 2;
export const INNER_TEN_RADIUS_CM = 2;
// Ring separator lines sit inside the higher-scoring ring they bound, so a
// line bounding a black ring has to be drawn light to stay visible at all.
export const RING_LINE_STROKE = "#1f2937";
export const RING_LINE_STROKE_ON_BLACK = "#ffffff";

// Matches backend/app/routes.py INNER_TEN_SCORE_RADIUS_CM = 2.339 exactly:
// INNER_TEN_RADIUS_CM (2) + ARROW_RADIUS_CM (0.279) + RING_LINE_SCORING_ALLOWANCE_CM (0.06) = 2.339
const SCORING_TOLERANCE_CM = 1e-9;

const GOLD_FILL = "#f4c54d";
const RED_FILL = "#d54a3f";
const BLUE_FILL = "#5c87c8";
const BLACK_FILL = "#1a1a1a";
const WHITE_FILL = "#ffffff";

const COMPOUND_RINGS: readonly TargetRing[] = [
  { score: 5, outerRadius: 24, fill: BLUE_FILL },
  { score: 6, outerRadius: 20, fill: BLUE_FILL },
  { score: 7, outerRadius: 16, fill: RED_FILL },
  { score: 8, outerRadius: 12, fill: RED_FILL },
  { score: 9, outerRadius: 8, fill: GOLD_FILL },
  { score: 10, outerRadius: 4, fill: GOLD_FILL },
];

const RECURVE_RINGS: readonly TargetRing[] = [
  { score: 1, outerRadius: 40, fill: WHITE_FILL },
  { score: 2, outerRadius: 36, fill: WHITE_FILL },
  { score: 3, outerRadius: 32, fill: BLACK_FILL },
  { score: 4, outerRadius: 28, fill: BLACK_FILL },
  { score: 5, outerRadius: 24, fill: BLUE_FILL },
  { score: 6, outerRadius: 20, fill: BLUE_FILL },
  { score: 7, outerRadius: 16, fill: RED_FILL },
  { score: 8, outerRadius: 12, fill: RED_FILL },
  { score: 9, outerRadius: 8, fill: GOLD_FILL },
  { score: 10, outerRadius: 4, fill: GOLD_FILL },
];

function buildTargetFaceConfig(
  type: TargetFaceType,
  descriptionLabel: string,
  rings: readonly TargetRing[]
): TargetFaceConfig {
  const scoringOuterRadius = Math.max(...rings.map((ring) => ring.outerRadius));
  const missGuideRadii: readonly [number, number] = [
    scoringOuterRadius + RING_WIDTH_CM,
    scoringOuterRadius + RING_WIDTH_CM * 2,
  ];

  return {
    type,
    descriptionLabel,
    rings,
    ringBoundaries: rings.map((ring) => ({
      radius: ring.outerRadius,
      stroke: ring.fill === BLACK_FILL ? RING_LINE_STROKE_ON_BLACK : RING_LINE_STROKE,
    })),
    scoringOuterRadius,
    missGuideRadii,
    maxPlottedRadius: missGuideRadii[1],
  };
}

export const TARGET_FACE_CONFIGS: Readonly<Record<TargetFaceType, TargetFaceConfig>> = {
  compound: buildTargetFaceConfig("compound", "six-ring compound", COMPOUND_RINGS),
  recurve: buildTargetFaceConfig("recurve", "ten-ring recurve", RECURVE_RINGS),
};

export function isTargetFaceType(value: unknown): value is TargetFaceType {
  return value === "compound" || value === "recurve";
}

function getScoringRadiusFromRadius(radius: number): number {
  return Math.max(radius - ARROW_RADIUS_CM - RING_LINE_SCORING_ALLOWANCE_CM, 0);
}

/**
 * An arrow touching a line scores the higher ring: the effective scoring
 * radius is shrunk by the arrow radius plus half the ring-line width before
 * comparing it against ring/inner-ten thresholds.
 */
export function isInnerTenPoint(point: TargetPoint): boolean {
  const radius = Math.hypot(point.x, point.y);
  return getScoringRadiusFromRadius(radius) <= INNER_TEN_RADIUS_CM;
}

export function scoreForPoint(config: TargetFaceConfig, point: TargetPoint): number {
  const radius = Math.hypot(point.x, point.y);
  const scoringRadius = getScoringRadiusFromRadius(radius);

  // config.rings is ordered ascending by score, i.e. descending by radius,
  // so the innermost ring (highest score, smallest outerRadius) is last.
  // Scan from the end to find the smallest outerRadius that still contains
  // the point, which is the actual score-bearing ring.
  for (let index = config.rings.length - 1; index >= 0; index -= 1) {
    const ring = config.rings[index];
    if (ring.outerRadius >= scoringRadius - SCORING_TOLERANCE_CM) {
      return ring.score;
    }
  }

  return 0;
}

export function getScoreColorBand(score: number): ScoreColorBand {
  if (score >= 9) {
    return "gold";
  }

  if (score >= 7) {
    return "red";
  }

  if (score >= 5) {
    return "blue";
  }

  if (score >= 3) {
    return "black";
  }

  if (score >= 1) {
    return "white";
  }

  return "miss";
}
