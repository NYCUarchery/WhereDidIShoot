import { describe, expect, it } from "vitest";
import {
  ARROW_RADIUS_CM,
  INNER_TEN_RADIUS_CM,
  RING_LINE_SCORING_ALLOWANCE_CM,
  RING_LINE_STROKE,
  RING_LINE_STROKE_ON_BLACK,
  RING_WIDTH_CM,
  TARGET_FACE_CONFIGS,
  getScoreColorBand,
  isInnerTenPoint,
  isTargetFaceType,
  scoreForPoint,
  type TargetPoint,
} from "./targetFaces";

// The amount a point's raw (nominal) radius may exceed a ring boundary while
// still counting as touching the higher-scoring ring, because the arrow
// shaft itself has width and the ring separator line has width too.
const SHRINK_CM = ARROW_RADIUS_CM + RING_LINE_SCORING_ALLOWANCE_CM;

// Cross-checked against backend/app/routes.py INNER_TEN_SCORE_RADIUS_CM = 2.339
const INNER_TEN_SCORE_RADIUS_CM = INNER_TEN_RADIUS_CM + SHRINK_CM;

function pointAtRadius(radius: number): TargetPoint {
  return { x: radius, y: 0 };
}

// Given a desired post-shrink "scoring radius" (the value the module
// actually compares against ring/inner-ten thresholds), return the raw
// point radius that produces it.
function rawRadiusForScoringRadius(scoringRadius: number): number {
  return scoringRadius + SHRINK_CM;
}

describe("INNER_TEN_SCORE_RADIUS_CM agreement with backend", () => {
  it("matches backend/app/routes.py INNER_TEN_SCORE_RADIUS_CM = 2.339", () => {
    expect(INNER_TEN_SCORE_RADIUS_CM).toBeCloseTo(2.339, 9);
  });

  it("is true for a point inside the inner-ten radius", () => {
    const point = pointAtRadius(INNER_TEN_SCORE_RADIUS_CM - 0.1);
    expect(isInnerTenPoint(point)).toBe(true);
  });

  it("is false for a point outside the inner-ten radius", () => {
    const point = pointAtRadius(INNER_TEN_SCORE_RADIUS_CM + 0.1);
    expect(isInnerTenPoint(point)).toBe(false);
  });

  it("is true exactly on the inner-ten boundary", () => {
    const point = pointAtRadius(INNER_TEN_SCORE_RADIUS_CM);
    expect(isInnerTenPoint(point)).toBe(true);
  });
});

describe("compound face scoring", () => {
  const config = TARGET_FACE_CONFIGS.compound;

  it.each(config.rings)(
    "scores $score for a point inside the $score ring",
    ({ score, outerRadius }) => {
      // Midpoint of the ring's width, safely away from either edge.
      const midScoringRadius = outerRadius - RING_WIDTH_CM / 2;
      const point = pointAtRadius(rawRadiusForScoringRadius(midScoringRadius));
      expect(scoreForPoint(config, point)).toBe(score);
    }
  );

  it("scores 0 just outside the 24 cm scoring outer radius", () => {
    const point = pointAtRadius(
      rawRadiusForScoringRadius(config.scoringOuterRadius) + 0.1
    );
    expect(scoreForPoint(config, point)).toBe(0);
  });
});

describe("recurve face scoring", () => {
  const config = TARGET_FACE_CONFIGS.recurve;

  it.each(config.rings)(
    "scores $score for a point inside the $score ring",
    ({ score, outerRadius }) => {
      const midScoringRadius = outerRadius - RING_WIDTH_CM / 2;
      const point = pointAtRadius(rawRadiusForScoringRadius(midScoringRadius));
      expect(scoreForPoint(config, point)).toBe(score);
    }
  );

  it("scores 0 just outside the 40 cm scoring outer radius", () => {
    const point = pointAtRadius(
      rawRadiusForScoringRadius(config.scoringOuterRadius) + 0.1
    );
    expect(scoreForPoint(config, point)).toBe(0);
  });
});

describe("line-touching ring boundaries", () => {
  const config = TARGET_FACE_CONFIGS.recurve;
  // The boundary between the score-5 ring (outerRadius 24) and the
  // score-6 ring (outerRadius 20): a shaft/line-width allowance applies at
  // the nominal radius of 20.
  const boundaryOuterRadius = 20;
  const higherScore = 6;
  const lowerScore = 5;

  it("scores the higher ring for a point clearly inside it", () => {
    const scoringRadius = boundaryOuterRadius - RING_WIDTH_CM / 2; // 18
    const point = pointAtRadius(rawRadiusForScoringRadius(scoringRadius));
    expect(scoreForPoint(config, point)).toBe(higherScore);
  });

  it("scores the lower ring for a point clearly inside it", () => {
    const scoringRadius = boundaryOuterRadius + RING_WIDTH_CM / 2; // 22
    const point = pointAtRadius(rawRadiusForScoringRadius(scoringRadius));
    expect(scoreForPoint(config, point)).toBe(lowerScore);
  });

  it("still scores the higher ring for a point whose raw radius is just outside the nominal boundary but within the shaft/line allowance", () => {
    // Raw (nominal, pre-shrink) radius is *beyond* the boundary, but the
    // full shrink allowance (arrow radius + half ring-line width) brings
    // the effective scoring radius back to exactly the boundary.
    const rawRadius = boundaryOuterRadius + SHRINK_CM;
    expect(rawRadius).toBeGreaterThan(boundaryOuterRadius);
    const point = pointAtRadius(rawRadius);
    expect(scoreForPoint(config, point)).toBe(higherScore);
  });
});

describe("miss guide radii", () => {
  it("compound exposes exactly [28, 32]", () => {
    expect(TARGET_FACE_CONFIGS.compound.missGuideRadii).toEqual([28, 32]);
  });

  it("recurve exposes exactly [44, 48]", () => {
    expect(TARGET_FACE_CONFIGS.recurve.missGuideRadii).toEqual([44, 48]);
  });
});

describe("getScoreColorBand", () => {
  it.each([
    [0, "miss"],
    [1, "white"],
    [2, "white"],
    [3, "black"],
    [4, "black"],
    [5, "blue"],
    [6, "blue"],
    [7, "red"],
    [8, "red"],
    [9, "gold"],
    [10, "gold"],
  ] as const)("maps score %i to %s", (score, band) => {
    expect(getScoreColorBand(score)).toBe(band);
  });

  it("maps scores 1-4 to white/black bands, not miss", () => {
    expect([1, 2, 3, 4].map(getScoreColorBand)).not.toContain("miss");
  });
});

describe("isTargetFaceType", () => {
  it("accepts the two known face types", () => {
    expect(isTargetFaceType("compound")).toBe(true);
    expect(isTargetFaceType("recurve")).toBe(true);
  });

  it.each([
    "olympic",
    "",
    "COMPOUND",
    0,
    1,
    null,
    undefined,
    {},
    ["compound"],
  ])("rejects %p", (value) => {
    expect(isTargetFaceType(value)).toBe(false);
  });
});

describe("ring separator strokes", () => {
  // A separator line sits inside the higher-scoring ring it bounds, so the
  // lines bounding the black 4 and 3 rings must be light or they vanish.
  it.each([
    [28, RING_LINE_STROKE_ON_BLACK],
    [32, RING_LINE_STROKE_ON_BLACK],
    [24, RING_LINE_STROKE],
    [36, RING_LINE_STROKE],
    [40, RING_LINE_STROKE],
    [4, RING_LINE_STROKE],
  ])("draws the recurve %p cm boundary in %s", (radius, stroke) => {
    const boundary = TARGET_FACE_CONFIGS.recurve.ringBoundaries.find(
      (item) => item.radius === radius
    );

    expect(boundary?.stroke).toBe(stroke);
  });

  it("keeps every compound boundary dark, as it has no black rings", () => {
    for (const boundary of TARGET_FACE_CONFIGS.compound.ringBoundaries) {
      expect(boundary.stroke).toBe(RING_LINE_STROKE);
    }
  });

  it("draws one boundary line per ring", () => {
    for (const config of Object.values(TARGET_FACE_CONFIGS)) {
      expect(config.ringBoundaries.map((boundary) => boundary.radius)).toEqual(
        config.rings.map((ring) => ring.outerRadius)
      );
    }
  });
});
