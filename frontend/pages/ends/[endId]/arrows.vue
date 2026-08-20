<script setup lang="ts">
import type { ArrowInput, ArrowRecord, EndRecord, PracticeRecord, RoundRecord } from "~/generated/sdk";

import { getErrorMessage, useArrowsApi, useEndsApi, usePracticesApi, useRoundsApi } from "~/lib/api";
import {
  ARROW_RADIUS_CM,
  INNER_TEN_RADIUS_CM,
  RING_LINE_STROKE,
  RING_LINE_WIDTH_CM,
  TARGET_FACE_CONFIGS,
  getScoreColorBand,
  isInnerTenPoint,
  isTargetFaceType,
  scoreForPoint,
  type TargetFaceConfig,
} from "~/lib/targetFaces";

type TargetPoint = {
  x: number;
  y: number;
};

type ViewBox = {
  minX: number;
  minY: number;
  width: number;
  height: number;
};

type PointerFraction = {
  x: number;
  y: number;
};

type ScoreMark = "" | "X" | "M";

const TARGET_CENTER_CROSS_LINE_WIDTH_CM = 0.1;
const TARGET_CENTER_CROSS_LINE_LENGTH_CM = 0.4;
const TARGET_CENTER_CROSS_HALF_LENGTH_CM = TARGET_CENTER_CROSS_LINE_LENGTH_CM / 2;
// Reference (compound-face) marker size/view-size figures. Placed-marker
// radius/font-size are scaled from these so they keep a constant on-screen
// size across faces with different view extents (see targetMarkerScale
// below); the compound face's scale factor is exactly 1 by construction.
const BASE_PLACED_MARKER_RADIUS_CM = 1;
const BASE_PLACED_MARKER_FONT_SIZE_CM = 1.28;
const DRAG_MARKER_FONT_SIZE_CM = 0.24;
const DRAG_MARKER_WIDE_FONT_SIZE_CM = 0.2;
const DRAG_THRESHOLD_PX = 2;
const TOUCH_TARGET_Y_OFFSET_CM = 2;
const DESKTOP_TARGET_Y_OFFSET_CM = 1;
const TARGET_VIEW_MARGIN_CM = 0.8;
const BASE_TARGET_VIEW_SIZE_CM =
  (TARGET_FACE_CONFIGS.compound.maxPlottedRadius +
    BASE_PLACED_MARKER_RADIUS_CM +
    TARGET_VIEW_MARGIN_CM) *
  2;
const DRAG_ZOOM_VIEW_SIZE_CM = 18;
const COORDINATE_PRECISION_DECIMALS = 3;
const COORDINATE_PRECISION_FACTOR = 10 ** COORDINATE_PRECISION_DECIMALS;
const MAX_ARROWS_PER_END = 6;
// The archery target face is nominally 80 cm regardless of practice
// distance/config; do not substitute the practice's target_face_cm here,
// as scoring geometry is not scaled by it (see TARGET_FACE_CONFIGS).
const TARGET_FACE_LABEL_CM = 80;

const route = useRoute();
const arrowsApi = useArrowsApi();
const endsApi = useEndsApi();
const roundsApi = useRoundsApi();
const practicesApi = usePracticesApi();

const targetSvg = ref<SVGSVGElement | null>(null);
const arrows = ref<ArrowRecord[]>([]);
const end = ref<EndRecord | null>(null);
const round = ref<RoundRecord | null>(null);
const practice = ref<PracticeRecord | null>(null);
const roundEnds = ref<EndRecord[]>([]);
const errorMessage = ref("");
const pending = ref(false);
const saving = ref(false);
const dragMode = ref<"create" | "update" | null>(null);
const activePointerId = ref<number | null>(null);
const activePointerType = ref<PointerEvent["pointerType"] | null>(null);
const dragArrowId = ref<number | null>(null);
const dragPoint = ref<TargetPoint | null>(null);
const dragStartClient = ref<{ x: number; y: number } | null>(null);
const dragPointerFraction = ref<PointerFraction | null>(null);
const dragMoved = ref(false);
const dragCommitOnRelease = ref(false);
const focusedArrowId = ref<number | null>(null);
const snackbar = reactive({ show: false, text: "" });
let nextOptimisticArrowId = -1;

const endId = computed(() => parseNumericId(route.params.endId));

const orderedArrows = computed(() =>
  [...arrows.value].sort(
    (left, right) => left.arrow_number - right.arrow_number || left.id - right.id
  )
);
const canCreateArrow = computed(() => orderedArrows.value.length < MAX_ARROWS_PER_END);
const totalScore = computed(() =>
  orderedArrows.value.reduce((sum, arrow) => sum + arrow.score, 0)
);
const currentEndIndex = computed(() =>
  end.value ? roundEnds.value.findIndex((item) => item.id === end.value.id) : -1
);
const previousEnd = computed(() =>
  currentEndIndex.value > 0 ? roundEnds.value[currentEndIndex.value - 1] : null
);
const nextEnd = computed(() =>
  currentEndIndex.value >= 0 && currentEndIndex.value < roundEnds.value.length - 1
    ? roundEnds.value[currentEndIndex.value + 1]
    : null
);
const dragArrowPoint = computed(() => getDragArrowPoint());
const focusedArrow = computed(
  () => orderedArrows.value.find((arrow) => arrow.id === focusedArrowId.value) ?? null
);
const liveDragLabel = computed(() => {
  if (!dragArrowPoint.value) {
    return null;
  }

  return isInnerTen(dragArrowPoint.value) ? "X" : String(getScore(dragArrowPoint.value));
});
const backToEndsLink = computed(() => {
  if (end.value) {
    return `/rounds/${end.value.round_id}`;
  }

  return "/";
});
const targetViewBox = computed(() => stringifyViewBox(getActiveTargetViewBox()));
const renderedDragPoint = computed(() => getRenderedDraftPoint());
const activeTargetFaceConfig = computed<TargetFaceConfig>(
  () => resolveTargetFaceConfig(practice.value) ?? TARGET_FACE_CONFIGS.compound
);
const targetViewExtentCm = computed(
  () =>
    activeTargetFaceConfig.value.maxPlottedRadius +
    BASE_PLACED_MARKER_RADIUS_CM +
    TARGET_VIEW_MARGIN_CM
);
const targetViewSizeCm = computed(() => targetViewExtentCm.value * 2);
const defaultTargetViewBox = computed<ViewBox>(() => ({
  minX: -targetViewExtentCm.value,
  minY: -targetViewExtentCm.value,
  width: targetViewSizeCm.value,
  height: targetViewSizeCm.value,
}));
// Placed-marker on-screen size scale factor: 1 for the compound face (its
// view size is exactly BASE_TARGET_VIEW_SIZE_CM by construction) and > 1 for
// faces with a larger view extent (e.g. recurve), so markers/digits keep a
// constant apparent size across faces instead of shrinking as the view grows.
const targetMarkerScale = computed(() => targetViewSizeCm.value / BASE_TARGET_VIEW_SIZE_CM);
const placedMarkerRadiusCm = computed(
  () => BASE_PLACED_MARKER_RADIUS_CM * targetMarkerScale.value
);
const placedMarkerFontSizeCm = computed(
  () => BASE_PLACED_MARKER_FONT_SIZE_CM * targetMarkerScale.value
);
const activeRingsDescending = computed(() =>
  [...activeTargetFaceConfig.value.rings].sort(
    (left, right) => right.outerRadius - left.outerRadius
  )
);
const activeRingBoundaries = computed(() => activeTargetFaceConfig.value.ringBoundaries);
const activeMissGuideRadii = computed(() => activeTargetFaceConfig.value.missGuideRadii);
const targetAriaLabel = computed(() => {
  const config = activeTargetFaceConfig.value;
  return `${TARGET_FACE_LABEL_CM} centimeter ${config.descriptionLabel} archery target face`;
});

function parseNumericId(value: unknown) {
  const raw = Array.isArray(value) ? value[0] : value;
  const parsed = Number(raw);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function resolveTargetFaceConfig(record: PracticeRecord | null): TargetFaceConfig | null {
  if (!record) {
    return null;
  }

  const rawTargetFaceType = record.target_face_type as unknown;
  if (rawTargetFaceType === undefined) {
    return TARGET_FACE_CONFIGS.compound;
  }

  return typeof rawTargetFaceType === "string" && isTargetFaceType(rawTargetFaceType)
    ? TARGET_FACE_CONFIGS[rawTargetFaceType]
    : null;
}

function notify(text: string) {
  snackbar.text = text;
  snackbar.show = true;
}

function roundCoordinate(value: number) {
  return Math.round(value * COORDINATE_PRECISION_FACTOR) / COORDINATE_PRECISION_FACTOR;
}

function clampUnitInterval(value: number) {
  return Math.min(Math.max(value, 0), 1);
}

function clampPointToRadius(point: TargetPoint, maxRadius: number) {
  const x = Number.isFinite(point.x) ? point.x : 0;
  const y = Number.isFinite(point.y) ? point.y : 0;
  const radius = Math.hypot(x, y);

  if (!radius || radius <= maxRadius) {
    return { x, y };
  }

  const scale = maxRadius / radius;
  return {
    x: x * scale,
    y: y * scale,
  };
}

function sanitizePoint(point: TargetPoint) {
  const clamped = clampPointToRadius(point, activeTargetFaceConfig.value.maxPlottedRadius);
  return {
    x: roundCoordinate(clamped.x),
    y: roundCoordinate(clamped.y),
  };
}

function isInnerTen(point: TargetPoint) {
  return isInnerTenPoint(point);
}

function getScore(point: TargetPoint) {
  return scoreForPoint(activeTargetFaceConfig.value, point);
}

function getScoreMark(point: TargetPoint): ScoreMark {
  if (isInnerTen(point)) {
    return "X";
  }

  return getScore(point) === 0 ? "M" : "";
}

function normalizeScoreMark(value: string | null | undefined): ScoreMark {
  const normalized = value?.trim().toUpperCase();
  if (normalized === "X" || normalized === "M") {
    return normalized;
  }

  return "";
}

function getArrowScoreMark(arrow: ArrowRecord): ScoreMark {
  const storedMark = normalizeScoreMark(arrow.score_mark);
  if (storedMark) {
    return storedMark;
  }

  if (arrow.score === 0) {
    return "M";
  }

  if (arrow.score === 10 && isInnerTen({ x: arrow.x, y: arrow.y })) {
    return "X";
  }

  return "";
}

function getScoreDisplay(score: number, scoreMark: ScoreMark) {
  return scoreMark || String(score);
}

function getArrowPayload(
  source: Pick<
    ArrowRecord,
    "arrow_number" | "end_id" | "notes" | "score_mark" | "x" | "y"
  >,
  point: TargetPoint,
  arrowNumber = source.arrow_number
): ArrowInput {
  const sanitized = sanitizePoint(point);
  const score = getScore(sanitized);
  const scoreMark = getScoreMark(sanitized);

  return {
    arrow_number: arrowNumber,
    end_id: source.end_id,
    notes: source.notes,
    score,
    score_mark: scoreMark,
    x: sanitized.x,
    y: sanitized.y,
  };
}

function nextArrowNumber() {
  return orderedArrows.value.length + 1;
}

function createOptimisticArrowRecord(payload: ArrowInput): ArrowRecord {
  return {
    id: nextOptimisticArrowId--,
    end_id: payload.end_id,
    arrow_number: payload.arrow_number,
    score: payload.score,
    score_mark: payload.score_mark ?? "",
    x: payload.x ?? 0,
    y: payload.y ?? 0,
    notes: payload.notes ?? "",
    created_at: new Date().toISOString(),
  };
}

function getActiveDragYOffset() {
  return dragMode.value
    ? getDragYOffsetForPointerType(activePointerType.value ?? "mouse")
    : 0;
}

function getDragYOffsetForPointerType(pointerType: PointerEvent["pointerType"]) {
  if (pointerType === "touch") {
    return TOUCH_TARGET_Y_OFFSET_CM;
  }

  return DESKTOP_TARGET_Y_OFFSET_CM;
}

function getPointerFractionFromEvent(event: PointerEvent) {
  const svg = targetSvg.value;
  if (!svg) {
    return null;
  }

  const rect = svg.getBoundingClientRect();
  if (!rect.width || !rect.height) {
    return null;
  }

  return {
    x: clampUnitInterval((event.clientX - rect.left) / rect.width),
    y: clampUnitInterval((event.clientY - rect.top) / rect.height),
  };
}

function clampViewBoxStart(value: number, size: number) {
  const extent = targetViewExtentCm.value;
  return Math.min(Math.max(value, -extent), extent - size);
}

function getActiveTargetViewBox(): ViewBox {
  if (!dragMode.value || !dragPoint.value || !dragPointerFraction.value) {
    return defaultTargetViewBox.value;
  }

  return {
    minX: clampViewBoxStart(
      dragPoint.value.x - dragPointerFraction.value.x * DRAG_ZOOM_VIEW_SIZE_CM,
      DRAG_ZOOM_VIEW_SIZE_CM
    ),
    minY: clampViewBoxStart(
      -dragPoint.value.y - dragPointerFraction.value.y * DRAG_ZOOM_VIEW_SIZE_CM,
      DRAG_ZOOM_VIEW_SIZE_CM
    ),
    width: DRAG_ZOOM_VIEW_SIZE_CM,
    height: DRAG_ZOOM_VIEW_SIZE_CM,
  };
}

function stringifyViewBox(viewBox: ViewBox) {
  return [viewBox.minX, viewBox.minY, viewBox.width, viewBox.height].join(" ");
}

function getPointFromEvent(event: PointerEvent, viewBox = defaultTargetViewBox.value) {
  const pointerFraction = getPointerFractionFromEvent(event);
  if (!pointerFraction) {
    return null;
  }

  const x = viewBox.minX + pointerFraction.x * viewBox.width;
  const y = -(viewBox.minY + pointerFraction.y * viewBox.height);

  return sanitizePoint({ x, y });
}

function getDragPointFromEvent(event: PointerEvent, viewBox = defaultTargetViewBox.value) {
  const point = getPointFromEvent(event, viewBox);
  if (!point) {
    return null;
  }

  return sanitizePoint({
    x: point.x,
    y: point.y - getDragYOffsetForPointerType(event.pointerType),
  });
}

function getDragArrowPoint() {
  if (!dragPoint.value) {
    return null;
  }

  return sanitizePoint({
    x: dragPoint.value.x,
    y: dragPoint.value.y + getActiveDragYOffset(),
  });
}

function getRenderedPoint(arrow: ArrowRecord) {
  if (dragArrowId.value === arrow.id && dragArrowPoint.value) {
    return dragArrowPoint.value;
  }

  return { x: arrow.x, y: arrow.y };
}

function getRenderedDraftPoint() {
  return dragArrowPoint.value;
}

function getPointLabel(point: TargetPoint) {
  return getScoreDisplay(getScore(point), getScoreMark(point));
}

function getScoreBadgeLabel(arrow: ArrowRecord) {
  return getScoreDisplay(arrow.score, getArrowScoreMark(arrow));
}

function getScoreBadgeClass(arrow: ArrowRecord) {
  return `score-badge--${getScoreColorBand(arrow.score)}`;
}

function getMarkerLabel(arrow: ArrowRecord) {
  if (
    dragMode.value === "update" &&
    dragArrowId.value === arrow.id &&
    dragArrowPoint.value
  ) {
    return getPointLabel(dragArrowPoint.value);
  }

  return String(arrow.arrow_number);
}

function getMarkerClassForPoint(point: TargetPoint) {
  return `target-marker--${getScoreColorBand(getScore(point))}`;
}

function getMarkerClass(arrow: ArrowRecord) {
  if (
    dragMode.value === "update" &&
    dragArrowId.value === arrow.id &&
    dragArrowPoint.value
  ) {
    return getMarkerClassForPoint(dragArrowPoint.value);
  }

  return "target-marker--ordered";
}

function isDraggedArrow(arrow: ArrowRecord) {
  return (
    dragMode.value === "update" && dragArrowId.value === arrow.id && dragArrowPoint.value
  );
}

function getMarkerRadius(arrow: ArrowRecord) {
  return isDraggedArrow(arrow) ? ARROW_RADIUS_CM : placedMarkerRadiusCm.value;
}

function getMarkerFontSize(label: string | null, isDragging = false) {
  if (!label) {
    return 0.24;
  }

  if (isDragging) {
    return label.length > 1 ? DRAG_MARKER_WIDE_FONT_SIZE_CM : DRAG_MARKER_FONT_SIZE_CM;
  }

  return placedMarkerFontSizeCm.value;
}

async function loadPage() {
  pending.value = true;
  errorMessage.value = "";
  end.value = null;
  round.value = null;
  practice.value = null;
  arrows.value = [];
  roundEnds.value = [];
  focusedArrowId.value = null;

  try {
    if (!endId.value) {
      throw new Error("Invalid end id.");
    }

    const currentEnd = await endsApi.get(endId.value);
    const roundPromise = roundsApi.get(currentEnd.round_id);
    const [currentRound, currentPractice, endArrows, siblingEnds] = await Promise.all([
      roundPromise,
      roundPromise.then((currentRoundResult) =>
        practicesApi.get(currentRoundResult.practice_id)
      ),
      arrowsApi.list({ end_id: endId.value }),
      endsApi.list({ round_id: currentEnd.round_id }),
    ]);

    if (!resolveTargetFaceConfig(currentPractice)) {
      const rawTargetFaceType = (currentPractice as { target_face_type?: unknown })
        .target_face_type;
      throw new Error(
        `This practice has an unrecognized target face type ("${String(
          rawTargetFaceType
        )}"). Update the practice before scoring arrows.`
      );
    }

    end.value = currentEnd;
    round.value = currentRound;
    practice.value = currentPractice;
    arrows.value = endArrows;
    roundEnds.value = siblingEnds;
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    pending.value = false;
  }
}

async function goToPreviousEnd() {
  if (!previousEnd.value || pending.value || saving.value) {
    return;
  }

  await navigateTo(`/ends/${previousEnd.value.id}/arrows`);
}

async function goToNextEnd() {
  if (!end.value || pending.value || saving.value) {
    return;
  }

  if (nextEnd.value) {
    await navigateTo(`/ends/${nextEnd.value.id}/arrows`);
    return;
  }

  saving.value = true;
  errorMessage.value = "";

  try {
    const createdEnd = await endsApi.create({
      notes: "",
      round_id: end.value.round_id,
    });
    await navigateTo(`/ends/${createdEnd.id}/arrows`);
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    saving.value = false;
  }
}

async function createArrow(point: TargetPoint) {
  if (!end.value || saving.value) {
    clearDragPreview();
    return;
  }

  if (!canCreateArrow.value) {
    clearDragPreview();
    return;
  }

  const payload = getArrowPayload(
    {
      arrow_number: nextArrowNumber(),
      end_id: end.value.id,
      notes: "",
      score_mark: "",
      x: point.x,
      y: point.y,
    },
    point
  );
  const optimisticArrow = createOptimisticArrowRecord(payload);

  arrows.value = [...arrows.value, optimisticArrow];
  clearDragPreview();
  saving.value = true;
  errorMessage.value = "";

  try {
    const createdArrow = await arrowsApi.create(payload);
    arrows.value = arrows.value.map((arrow) =>
      arrow.id === optimisticArrow.id ? createdArrow : arrow
    );
  } catch (error) {
    arrows.value = arrows.value.filter((arrow) => arrow.id !== optimisticArrow.id);
    errorMessage.value = getErrorMessage(error);
  } finally {
    saving.value = false;
  }
}

async function updateArrowPosition(arrowId: number, point: TargetPoint) {
  if (saving.value) {
    clearDragPreview();
    return;
  }

  const arrowIndex = arrows.value.findIndex((item) => item.id === arrowId);
  const arrow = arrowIndex >= 0 ? arrows.value[arrowIndex] : null;
  if (!arrow) {
    clearDragPreview();
    return;
  }

  const payload = getArrowPayload(arrow, point);
  const optimisticArrow: ArrowRecord = {
    ...arrow,
    ...payload,
    x: payload.x ?? arrow.x,
    y: payload.y ?? arrow.y,
    notes: payload.notes ?? arrow.notes,
  };

  arrows.value = arrows.value.map((item, index) =>
    index === arrowIndex ? optimisticArrow : item
  );
  clearDragPreview();
  saving.value = true;
  errorMessage.value = "";

  try {
    const updatedArrow = await arrowsApi.update(arrow.id, payload);
    arrows.value = arrows.value.map((item) => (item.id === arrow.id ? updatedArrow : item));
  } catch (error) {
    arrows.value = arrows.value.map((item) => (item.id === arrow.id ? arrow : item));
    errorMessage.value = getErrorMessage(error);
  } finally {
    saving.value = false;
  }
}

function getResequencedArrowRecords(records: ArrowRecord[]) {
  return [...records]
    .sort((left, right) => left.arrow_number - right.arrow_number || left.id - right.id)
    .map((item, index) => {
      const nextNumber = index + 1;
      return item.arrow_number === nextNumber
        ? item
        : {
            ...item,
            arrow_number: nextNumber,
          };
    });
}

async function resequenceArrows(records: ArrowRecord[]) {
  const updates = getResequencedArrowRecords(records)
    .map((arrow) => {
      const original = records.find((item) => item.id === arrow.id);
      if (!original || original.arrow_number === arrow.arrow_number) {
        return null;
      }

      return arrowsApi.update(
        arrow.id,
        getArrowPayload(arrow, { x: arrow.x, y: arrow.y }, arrow.arrow_number)
      );
    })
    .filter((request): request is Promise<ArrowRecord> => Boolean(request));

  return updates.length > 0 ? Promise.all(updates) : [];
}

async function deleteArrow(arrow: ArrowRecord) {
  if (saving.value) {
    return;
  }

  const previousArrows = [...arrows.value];
  const remaining = arrows.value.filter((item) => item.id !== arrow.id);
  const resequencedRemaining = getResequencedArrowRecords(remaining);

  arrows.value = resequencedRemaining;
  saving.value = true;
  errorMessage.value = "";

  try {
    await arrowsApi.remove(arrow.id);
    const updatedArrows = await resequenceArrows(remaining);
    if (updatedArrows.length > 0) {
      const updatedArrowMap = new Map(updatedArrows.map((item) => [item.id, item]));
      arrows.value = arrows.value.map((item) => updatedArrowMap.get(item.id) ?? item);
    }
  } catch (error) {
    arrows.value = previousArrows;
    errorMessage.value = getErrorMessage(error);
  } finally {
    saving.value = false;
  }
}

async function deleteFocusedArrow() {
  const arrow = focusedArrow.value;
  if (!arrow) {
    return;
  }

  await deleteArrow(arrow);

  // deleteArrow's optimistic removal trips the stale-focus watcher; if the
  // request failed the arrow is rolled back, so restore focus rather than
  // dropping the user's editing context on an error they can retry.
  if (arrows.value.some((item) => item.id === arrow.id)) {
    focusedArrowId.value = arrow.id;
  }
}

function startDragging(pointerId: number, pointerType: PointerEvent["pointerType"]) {
  activePointerId.value = pointerId;
  activePointerType.value = pointerType;

  if (import.meta.client) {
    window.addEventListener("pointermove", handleWindowPointerMove);
    window.addEventListener("pointerup", handleWindowPointerUp);
    window.addEventListener("pointercancel", handleWindowPointerCancel);
  }
}

function beginFocusedArrowRelocate(arrowId: number, event: PointerEvent) {
  const point = getDragPointFromEvent(event);
  if (!point) {
    return;
  }

  dragMode.value = "update";
  dragArrowId.value = arrowId;
  dragPoint.value = point;
  dragStartClient.value = { x: event.clientX, y: event.clientY };
  dragPointerFraction.value = getPointerFractionFromEvent(event);
  dragMoved.value = false;
  // A bare tap is an explicit relocate gesture in focus mode, so it commits
  // without the drag-distance requirement that guards marker dragging.
  dragCommitOnRelease.value = true;
  startDragging(event.pointerId, event.pointerType);
}

function handleTargetPointerDown(event: PointerEvent) {
  if (saving.value || activePointerId.value !== null || dragMode.value) {
    return;
  }

  if (focusedArrowId.value !== null) {
    // While an arrow is focused the whole target face relocates that arrow
    // instead of creating a new one, so this path deliberately skips the
    // canCreateArrow guard: a full end can still be corrected.
    beginFocusedArrowRelocate(focusedArrowId.value, event);
    return;
  }

  if (!canCreateArrow.value) {
    return;
  }

  const point = getDragPointFromEvent(event);
  if (!point) {
    return;
  }

  dragMode.value = "create";
  dragArrowId.value = null;
  dragPoint.value = point;
  dragStartClient.value = { x: event.clientX, y: event.clientY };
  dragPointerFraction.value = getPointerFractionFromEvent(event);
  dragMoved.value = false;
  dragCommitOnRelease.value = false;
  startDragging(event.pointerId, event.pointerType);
}

function handleMarkerPointerDown(arrow: ArrowRecord, event: PointerEvent) {
  if (saving.value || activePointerId.value !== null || dragMode.value) {
    return;
  }

  // In focus mode the placed markers are part of the relocate surface too, so
  // a press anywhere — including on top of another marker — moves the focused
  // arrow rather than grabbing whichever marker is under the pointer.
  if (focusedArrowId.value !== null) {
    beginFocusedArrowRelocate(focusedArrowId.value, event);
    return;
  }

  const point = getDragPointFromEvent(event);
  if (!point) {
    return;
  }

  dragMode.value = "update";
  dragArrowId.value = arrow.id;
  dragPoint.value = point;
  dragStartClient.value = { x: event.clientX, y: event.clientY };
  dragPointerFraction.value = getPointerFractionFromEvent(event);
  dragMoved.value = false;
  dragCommitOnRelease.value = false;
  startDragging(event.pointerId, event.pointerType);
}

function toggleFocusedArrow(arrow: ArrowRecord) {
  if (saving.value) {
    return;
  }

  if (focusedArrowId.value === arrow.id) {
    clearFocusedArrow();
    return;
  }

  focusedArrowId.value = arrow.id;
}

function clearFocusedArrow() {
  // Abandon an in-flight relocate of the focused arrow: without this, Escape
  // or Done reads as "cancel" but the pending pointerup would still commit the
  // move (dragCommitOnRelease makes it commit even with no movement).
  if (
    focusedArrowId.value !== null &&
    dragMode.value === "update" &&
    dragArrowId.value === focusedArrowId.value
  ) {
    stopDragging();
  }

  focusedArrowId.value = null;
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === "Escape") {
    clearFocusedArrow();
  }
}

function clearDragPreview() {
  dragMode.value = null;
  dragArrowId.value = null;
  dragPoint.value = null;
  dragPointerFraction.value = null;
}

function stopPointerTracking() {
  activePointerId.value = null;
  activePointerType.value = null;
  dragStartClient.value = null;
  dragMoved.value = false;
  dragCommitOnRelease.value = false;

  if (import.meta.client) {
    window.removeEventListener("pointermove", handleWindowPointerMove);
    window.removeEventListener("pointerup", handleWindowPointerUp);
    window.removeEventListener("pointercancel", handleWindowPointerCancel);
  }
}

function stopDragging() {
  clearDragPreview();
  stopPointerTracking();
}

function handleWindowPointerMove(event: PointerEvent) {
  if (activePointerId.value !== event.pointerId || !dragMode.value) {
    return;
  }

  if (dragStartClient.value) {
    const distance = Math.hypot(
      event.clientX - dragStartClient.value.x,
      event.clientY - dragStartClient.value.y
    );
    if (distance >= DRAG_THRESHOLD_PX) {
      dragMoved.value = true;
    }
  }

  const point = getDragPointFromEvent(event);
  const pointerFraction = getPointerFractionFromEvent(event);
  if (!point || !pointerFraction) {
    return;
  }

  dragPoint.value = point;
  dragPointerFraction.value = pointerFraction;
}

async function handleWindowPointerUp(event: PointerEvent) {
  if (activePointerId.value !== event.pointerId || !dragMode.value) {
    return;
  }

  const mode = dragMode.value;
  const arrowId = dragArrowId.value;
  const point = getDragArrowPoint();
  const moved = dragMoved.value;
  const commitOnRelease = dragCommitOnRelease.value;

  stopPointerTracking();

  if (!point) {
    clearDragPreview();
    return;
  }

  if (mode === "create") {
    await createArrow(point);
    return;
  }

  if (!arrowId) {
    clearDragPreview();
    return;
  }

  if (!moved && !commitOnRelease) {
    clearDragPreview();
    return;
  }

  await updateArrowPosition(arrowId, point);
}

function handleWindowPointerCancel(event: PointerEvent) {
  if (activePointerId.value !== event.pointerId) {
    return;
  }

  stopDragging();
}

watch(
  () => route.params.endId,
  () => {
    loadPage();
  }
);

watch(orderedArrows, (records) => {
  if (
    focusedArrowId.value !== null &&
    !records.some((arrow) => arrow.id === focusedArrowId.value)
  ) {
    focusedArrowId.value = null;
  }
});

onMounted(() => {
  window.addEventListener("keydown", handleKeyDown);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleKeyDown);
});

onBeforeUnmount(stopDragging);

await loadPage();
</script>

<template>
  <div class="arrows-screen">
    <v-alert
      v-if="errorMessage"
      class="mb-2"
      color="error"
      variant="tonal"
    >
      {{ errorMessage }}
    </v-alert>

    <template v-if="end">
      <div class="stage-stack">
        <div class="toolbar-row">
          <div class="toolbar-actions">
            <v-btn icon="mdi-arrow-left" :to="backToEndsLink" variant="text" />
            <div class="toolbar-copy">
              <p class="eyebrow mb-0">
                Round {{ round?.round_order ?? "?" }} · End {{ end.end_number }}
              </p>
            </div>
          </div>
          <div class="toolbar-meta">
            <div class="toolbar-total">
              <span class="toolbar-total__label">Total</span>
              <strong>{{ totalScore }}</strong>
            </div>
            <v-progress-circular
              v-if="pending || saving"
              color="primary"
              indeterminate
              size="26"
            />
          </div>
        </div>

        <section class="target-stage">
          <div class="stage-topbar">
            <div class="score-strip">
              <div v-for="arrow in orderedArrows" :key="arrow.id" class="score-entry">
                <button
                  class="score-badge"
                  :class="[
                    getScoreBadgeClass(arrow),
                    { 'score-badge--focused': focusedArrowId === arrow.id },
                  ]"
                  type="button"
                  :aria-pressed="focusedArrowId === arrow.id"
                  :aria-label="`Adjust arrow ${arrow.arrow_number}, score ${getScoreBadgeLabel(arrow)}`"
                  :aria-disabled="saving"
                  @click="toggleFocusedArrow(arrow)"
                >
                  <span class="score-order">{{ arrow.arrow_number }}</span>
                  {{ getScoreBadgeLabel(arrow) }}
                </button>
              </div>

              <div v-if="!pending && orderedArrows.length === 0" class="score-empty">
                Tap the target to add the first arrow
              </div>

              <div
                v-else-if="orderedArrows.length >= MAX_ARROWS_PER_END"
                class="score-empty"
              >
                End full: 6 arrows max
              </div>
            </div>

            <button
              v-if="orderedArrows.length > 0"
              class="stage-backspace"
              type="button"
              aria-label="Delete last arrow"
              @click="deleteArrow(orderedArrows[orderedArrows.length - 1])"
            >
              <v-icon icon="mdi-backspace-outline" size="24" />
            </button>
          </div>

          <div class="stage-status">
            <div v-if="focusedArrow" class="focus-bar">
              <span class="focus-bar__label">Arrow {{ focusedArrow.arrow_number }}</span>
              <span class="focus-bar__score" :class="getScoreBadgeClass(focusedArrow)">
                {{ getScoreBadgeLabel(focusedArrow) }}
              </span>
              <span class="focus-bar__coords">
                x {{ focusedArrow.x.toFixed(COORDINATE_PRECISION_DECIMALS) }}
                y {{ focusedArrow.y.toFixed(COORDINATE_PRECISION_DECIMALS) }}
              </span>
              <span class="focus-bar__hint">Tap or drag the target to move this arrow</span>
              <div class="focus-bar__actions">
                <v-btn
                  :disabled="saving"
                  size="small"
                  variant="text"
                  @click="deleteFocusedArrow"
                >
                  Delete
                </v-btn>
                <v-btn color="primary" size="small" variant="tonal" @click="clearFocusedArrow">
                  Done
                </v-btn>
              </div>
            </div>
            <!--
              The score chip renders unconditionally (blank while idle, with the
              whole readout visibility:hidden then) because it is the tallest
              child and so it alone sets this row's height. Gating it on
              dragArrowPoint grew the row on the very pointerdown that starts a
              drag, which pushed the SVG down after dragPointerFraction had been
              captured against the pre-shift rect, rendering the marker below
              the pressed point until the first pointermove re-anchored it.
              .stage-status's min-height used to absorb that growth; it no
              longer can once the focus bar adds a second row.
            -->
            <div class="drag-coordinates" :class="{ 'drag-coordinates--hidden': !dragArrowPoint }">
              <span class="drag-coordinates__score">{{ liveDragLabel }}</span>
              <template v-if="dragArrowPoint">
                <span>x {{ dragArrowPoint.x.toFixed(COORDINATE_PRECISION_DECIMALS) }}</span>
                <span>y {{ dragArrowPoint.y.toFixed(COORDINATE_PRECISION_DECIMALS) }}</span>
              </template>
            </div>
          </div>

          <div class="target-shell">
            <svg
              ref="targetSvg"
              class="target-svg"
              :viewBox="targetViewBox"
              role="img"
              :aria-label="targetAriaLabel"
              @pointerdown="handleTargetPointerDown"
            >
              <circle
                v-for="ring in activeRingsDescending"
                :key="ring.score"
                cx="0"
                cy="0"
                :r="ring.outerRadius"
                :fill="ring.fill"
              />

              <circle
                v-for="boundary in activeRingBoundaries"
                :key="boundary.radius"
                cx="0"
                cy="0"
                :r="boundary.radius"
                fill="none"
                :stroke="boundary.stroke"
                :stroke-width="RING_LINE_WIDTH_CM"
              />
              <circle
                cx="0"
                cy="0"
                :r="INNER_TEN_RADIUS_CM"
                fill="none"
                :stroke="RING_LINE_STROKE"
                :stroke-width="RING_LINE_WIDTH_CM"
              />
              <g class="target-center-cross" aria-hidden="true">
                <line
                  :x1="-TARGET_CENTER_CROSS_HALF_LENGTH_CM"
                  y1="0"
                  :x2="TARGET_CENTER_CROSS_HALF_LENGTH_CM"
                  y2="0"
                  stroke="#1f2937"
                  :stroke-width="TARGET_CENTER_CROSS_LINE_WIDTH_CM"
                  stroke-linecap="square"
                />
                <line
                  x1="0"
                  :y1="-TARGET_CENTER_CROSS_HALF_LENGTH_CM"
                  x2="0"
                  :y2="TARGET_CENTER_CROSS_HALF_LENGTH_CM"
                  stroke="#1f2937"
                  :stroke-width="TARGET_CENTER_CROSS_LINE_WIDTH_CM"
                  stroke-linecap="square"
                />
              </g>
              <circle
                v-for="radius in activeMissGuideRadii"
                :key="`miss-${radius}`"
                class="target-miss-guide"
                cx="0"
                cy="0"
                :r="radius"
                fill="none"
                stroke="#4b5563"
                :stroke-width="RING_LINE_WIDTH_CM"
                stroke-dasharray="0.5 0.4"
              />

              <g
                v-for="arrow in orderedArrows"
                :key="arrow.id"
                class="target-marker"
                :class="[
                  getMarkerClass(arrow),
                  {
                    'target-marker--selected':
                      dragArrowId === arrow.id && dragMode === 'update',
                    'target-marker--focused': focusedArrowId === arrow.id,
                    'target-marker--muted':
                      focusedArrowId !== null && focusedArrowId !== arrow.id,
                  },
                ]"
                :transform="`translate(${getRenderedPoint(arrow).x} ${-getRenderedPoint(
                  arrow
                ).y})`"
                @pointerdown.stop.prevent="handleMarkerPointerDown(arrow, $event)"
              >
                <circle
                  v-if="isDraggedArrow(arrow) || focusedArrowId === arrow.id"
                  class="target-marker__halo"
                  :r="getMarkerRadius(arrow)"
                />
                <circle class="target-marker__badge" :r="getMarkerRadius(arrow)" />
                <text
                  class="target-marker__label"
                  text-anchor="middle"
                  dominant-baseline="central"
                  :font-size="
                    getMarkerFontSize(getMarkerLabel(arrow), isDraggedArrow(arrow))
                  "
                >
                  {{ getMarkerLabel(arrow) }}
                </text>
              </g>

              <g
                v-if="dragMode === 'create' && renderedDragPoint"
                class="target-marker target-marker--draft"
                :class="getMarkerClassForPoint(renderedDragPoint)"
                :transform="
                  renderedDragPoint
                    ? `translate(${renderedDragPoint.x} ${-renderedDragPoint.y})`
                    : ''
                "
              >
                <circle class="target-marker__halo" :r="ARROW_RADIUS_CM" />
                <circle class="target-marker__badge" :r="ARROW_RADIUS_CM" />
                <text
                  class="target-marker__label"
                  text-anchor="middle"
                  dominant-baseline="central"
                  :font-size="getMarkerFontSize(liveDragLabel, true)"
                >
                  {{ liveDragLabel }}
                </text>
              </g>
            </svg>
          </div>

          <div class="stage-nav">
            <v-btn
              prepend-icon="mdi-chevron-left"
              :disabled="!previousEnd || pending || saving"
              size="small"
              variant="outlined"
              @click="goToPreviousEnd"
            >
              Last End
            </v-btn>
            <v-btn
              append-icon="mdi-chevron-right"
              :disabled="pending || saving"
              color="primary"
              size="small"
              variant="outlined"
              @click="goToNextEnd"
            >
              Next End
            </v-btn>
          </div>
        </section>
      </div>
    </template>
    <div v-else-if="!pending" class="error-recovery">
      <v-btn color="primary" prepend-icon="mdi-arrow-left" :to="backToEndsLink" variant="tonal">
        Back
      </v-btn>
    </div>

    <v-snackbar v-model="snackbar.show" color="secondary">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<style scoped>
.arrows-screen {
  display: grid;
  gap: 0.8rem;
  -webkit-user-select: none;
  user-select: none;
}

.error-recovery {
  display: flex;
  justify-content: flex-start;
}

.toolbar-row,
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}

.toolbar-row {
  justify-content: space-between;
}

.toolbar-actions {
  min-width: 0;
}

.toolbar-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.toolbar-copy {
  min-width: 0;
}

.toolbar-total {
  display: inline-flex;
  align-items: baseline;
  gap: 0.45rem;
  padding: 0.45rem 0.75rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  color: #111827;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.08);
}

.toolbar-total__label {
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(17, 24, 39, 0.58);
}

.toolbar-total strong {
  font-family: "Avenir Next Condensed", "Gill Sans", "Trebuchet MS", sans-serif;
  font-size: 1.45rem;
  line-height: 1;
}

.toolbar-copy h1 {
  margin: 0;
  font-family: "Avenir Next Condensed", "Gill Sans", "Trebuchet MS", sans-serif;
  font-size: clamp(1.9rem, 4vw, 2.5rem);
  line-height: 1;
}

.stage-stack {
  display: grid;
  gap: 1rem;
}

.target-stage {
  display: grid;
  gap: 0.9rem;
  overflow: hidden;
  border: 1px solid rgba(var(--wdis-ink-rgb), 0.08);
  border-radius: 1.75rem;
  background: radial-gradient(
    circle at top,
    rgba(255, 255, 255, 0.95),
    rgba(244, 240, 234, 0.92) 56%,
    rgba(237, 232, 224, 0.9) 100%
  );
  box-shadow: 0 24px 48px rgba(var(--wdis-ink-rgb), 0.08);
  padding: clamp(1rem, 3vw, 1.75rem);
}

.stage-topbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.85rem;
  align-items: start;
}

.score-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  align-items: center;
  min-width: 0;
}

.score-entry {
  position: relative;
  display: inline-flex;
}

.score-order {
  position: absolute;
  top: -0.35rem;
  left: -0.35rem;
  z-index: 1;
  width: 1.15rem;
  height: 1.15rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: #1f5c3f;
  color: #ffffff;
  box-shadow: 0 6px 12px rgba(17, 24, 39, 0.16);
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1;
  text-align: center;
}

.score-badge {
  position: relative;
  width: 2.55rem;
  height: 2.55rem;
  padding: 0;
  border: 0;
  border-radius: 999px;
  display: grid;
  place-items: center;
  appearance: none;
  font-family: "Avenir Next Condensed", "Gill Sans", "Trebuchet MS", sans-serif;
  font-size: 1.45rem;
  line-height: 1;
  color: #111827;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.08);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, outline-color 0.18s ease;
}

.score-badge:hover {
  transform: translateY(-1px);
}

.score-badge[aria-disabled="true"] {
  cursor: default;
  opacity: 0.55;
}

.score-badge--focused {
  outline: 3px solid #1f5c3f;
  outline-offset: 2px;
}

.score-badge--gold {
  background: #f7eb4c;
}

.score-badge--red {
  background: #de5b50;
  color: #ffffff;
}

.score-badge--blue {
  background: #55a5e2;
  color: #ffffff;
}

.score-badge--black {
  background: #1a1a1a;
  color: #ffffff;
}

.score-badge--white {
  background: #ffffff;
  color: #111827;
  border: 1px solid rgba(17, 24, 39, 0.35);
}

.score-badge--miss {
  background: #d1d5db;
  color: #111827;
}

.score-empty {
  font-size: 0.98rem;
  color: rgba(17, 24, 39, 0.6);
  padding: 0.4rem 0.1rem;
}

.stage-backspace {
  width: 3rem;
  height: 3rem;
  border: 0;
  border-radius: 0.9rem;
  display: grid;
  place-items: center;
  background: rgba(17, 24, 39, 0.58);
  color: #ffffff;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.12);
}

.stage-status {
  min-height: 2.8rem;
  display: grid;
  gap: 0.55rem;
}

.focus-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem;
  padding: 0.5rem 0.6rem 0.5rem 0.85rem;
  border-radius: 0.85rem;
  background: rgba(31, 92, 63, 0.1);
  color: #111827;
  font-size: 0.95rem;
}

.focus-bar__label {
  font-weight: 700;
}

.focus-bar__score {
  width: 1.9rem;
  height: 1.9rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-size: 1.05rem;
  line-height: 1;
  box-shadow: none;
}

.focus-bar__coords {
  color: rgba(17, 24, 39, 0.7);
  font-variant-numeric: tabular-nums;
}

.focus-bar__hint {
  color: rgba(17, 24, 39, 0.6);
}

.focus-bar__actions {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-left: auto;
}

.drag-coordinates {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.55rem 0.8rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.88);
  color: #111827;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.1);
  font-size: 0.95rem;
  backdrop-filter: blur(10px);
  justify-self: end;
}

.drag-coordinates--hidden {
  visibility: hidden;
  pointer-events: none;
}

.drag-coordinates__score {
  min-width: 1.7rem;
  height: 1.7rem;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(17, 24, 39, 0.9);
  color: #ffffff;
  font-family: "Avenir Next Condensed", "Gill Sans", "Trebuchet MS", sans-serif;
  font-size: 1rem;
  line-height: 1;
}

.target-shell {
  display: grid;
  place-items: center;
  min-height: 0;
}

.stage-nav {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
}

.target-svg {
  display: block;
  width: min(100%, 62rem);
  max-width: 100%;
  height: auto;
  cursor: crosshair;
  touch-action: none;
}

.target-miss-guide {
  opacity: 0.42;
}

.target-center-cross {
  pointer-events: none;
}

.target-marker {
  cursor: grab;
  touch-action: none;
}

.target-marker:active {
  cursor: grabbing;
}

.target-marker__badge {
  fill: rgba(17, 24, 39, 0.86);
  transition: transform 0.18s ease, fill 0.18s ease;
}

/*
 * White halo painted underneath the badge, only ever present in the DOM for
 * an actively dragged/created marker or the focused marker (see the
 * `v-if="isDraggedArrow(arrow) || focusedArrowId === arrow.id"` and the
 * create-draft `<g>` in the template). It never exists for other placed,
 * non-dragged, non-focused markers, so their rendering is untouched by this
 * rule. It separates a dragged/focused marker's fill from a same-hue ring
 * behind it (notably gold-on-gold) beyond what the thin selected/draft
 * stroke alone provides.
 */
.target-marker__halo {
  fill: none;
  stroke: #ffffff;
  stroke-width: 0.3;
  pointer-events: none;
}

.target-marker__label {
  fill: #ffffff;
  font-family: "Avenir Next Condensed", "Gill Sans", "Trebuchet MS", sans-serif;
  font-weight: 700;
  line-height: 1;
  user-select: none;
  letter-spacing: -0.04em;
  pointer-events: none;
}

.target-marker--ordered .target-marker__badge {
  fill: rgba(17, 24, 39, 0.84);
}

.target-marker--gold .target-marker__badge {
  fill: #f7eb4c;
}

.target-marker--gold .target-marker__label,
.target-marker--miss .target-marker__label {
  fill: #111827;
}

.target-marker--red .target-marker__badge {
  fill: #de5b50;
}

.target-marker--blue .target-marker__badge {
  fill: #55a5e2;
}

.target-marker--black .target-marker__badge {
  fill: #1a1a1a;
}

.target-marker--white .target-marker__badge {
  fill: #ffffff;
  stroke: #111827;
  stroke-width: 0.08;
}

.target-marker--white .target-marker__label {
  fill: #111827;
}

.target-marker--miss .target-marker__badge {
  fill: #d1d5db;
}

/*
 * Non-focused markers are dimmed (not hidden) while one arrow is focused, so
 * the group stays readable as context while the focused marker reads as the
 * only live target.
 */
.target-marker--muted {
  opacity: 0.38;
}

/*
 * Selected/draft/focused is a highlight affordance layered on top of the
 * per-score colour, not a replacement for it: only `stroke` is set here so
 * the ring's gold/red/blue/black/white/miss fill (and matching label colour)
 * always shows through while a marker is being placed, dragged, or focused.
 */
.target-marker--selected .target-marker__badge,
.target-marker--draft .target-marker__badge,
.target-marker--focused .target-marker__badge {
  stroke: #1f5c3f;
  stroke-width: 0.16;
}

@media (max-width: 720px) {
  .target-stage {
    border-radius: 1.2rem;
    gap: 0.75rem;
  }

  .stage-topbar {
    gap: 0.7rem;
  }

  .score-strip {
    gap: 0.55rem;
  }

  .score-entry {
    position: relative;
  }

  .score-order {
    top: -0.28rem;
    left: -0.28rem;
    width: 1rem;
    height: 1rem;
    font-size: 0.64rem;
  }

  .score-badge {
    width: 2.15rem;
    height: 2.15rem;
    font-size: 1.2rem;
  }

  .stage-backspace {
    width: 2.7rem;
    height: 2.7rem;
  }

  .toolbar-meta {
    gap: 0.55rem;
  }

  .stage-nav {
    gap: 0.55rem;
    margin-top: 0.8rem;
  }

  .toolbar-total {
    padding: 0.38rem 0.62rem;
  }

  .toolbar-total strong {
    font-size: 1.22rem;
  }

  .drag-coordinates {
    gap: 0.45rem;
    padding: 0.48rem 0.7rem;
    font-size: 0.84rem;
  }

  .focus-bar {
    font-size: 0.84rem;
    padding: 0.45rem 0.5rem 0.45rem 0.7rem;
  }

  .focus-bar__coords,
  .focus-bar__hint {
    display: none;
  }

  .stage-nav {
    flex-wrap: wrap;
  }
}
</style>
