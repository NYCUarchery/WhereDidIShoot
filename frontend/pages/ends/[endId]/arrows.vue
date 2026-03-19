<script setup lang="ts">
import type { ArrowInput, ArrowRecord, EndRecord, RoundRecord } from "~/generated/sdk";

import { getErrorMessage, useArrowsApi, useEndsApi, useRoundsApi } from "~/lib/api";

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

const SIX_RING_OUTER_RADIUS_CM = 24;
const TARGET_DIAMETER_CM = SIX_RING_OUTER_RADIUS_CM * 2;
const TARGET_RADIUS_CM = TARGET_DIAMETER_CM / 2;
const RING_WIDTH_CM = 4;
const OUTSIDE_TARGET_RING_COUNT = 2;
const MAX_PLOTTED_RADIUS_CM = TARGET_RADIUS_CM + RING_WIDTH_CM * OUTSIDE_TARGET_RING_COUNT;
const INNER_TEN_RADIUS_CM = 2;
const TARGET_CENTER_CROSS_LINE_WIDTH_CM = 0.1;
const TARGET_CENTER_CROSS_LINE_LENGTH_CM = 0.4;
const TARGET_CENTER_CROSS_HALF_LENGTH_CM = TARGET_CENTER_CROSS_LINE_LENGTH_CM / 2;
const RING_LINE_WIDTH_CM = 0.12;
const RING_LINE_SCORING_ALLOWANCE_CM = RING_LINE_WIDTH_CM / 2;
const SCORING_TOLERANCE_CM = 1e-9;
const ARROW_DIAMETER_CM = 0.558;
const ARROW_RADIUS_CM = ARROW_DIAMETER_CM / 2;
const PLACED_MARKER_RADIUS_CM = 1;
const DRAG_MARKER_FONT_SIZE_CM = 0.24;
const DRAG_MARKER_WIDE_FONT_SIZE_CM = 0.2;
const PLACED_MARKER_FONT_SIZE_CM = 1.28;
const DRAG_THRESHOLD_PX = 2;
const TOUCH_TARGET_Y_OFFSET_CM = 2;
const DESKTOP_TARGET_Y_OFFSET_CM = 1;
const TARGET_VIEW_MARGIN_CM = 0.8;
const TARGET_VIEW_EXTENT_CM =
  MAX_PLOTTED_RADIUS_CM + PLACED_MARKER_RADIUS_CM + TARGET_VIEW_MARGIN_CM;
const TARGET_VIEW_SIZE_CM = TARGET_VIEW_EXTENT_CM * 2;
const DRAG_ZOOM_VIEW_SIZE_CM = 18;
const COORDINATE_PRECISION_DECIMALS = 3;
const COORDINATE_PRECISION_FACTOR = 10 ** COORDINATE_PRECISION_DECIMALS;
const MAX_ARROWS_PER_END = 6;
const DEFAULT_TARGET_VIEW_BOX: ViewBox = {
  minX: -TARGET_VIEW_EXTENT_CM,
  minY: -TARGET_VIEW_EXTENT_CM,
  width: TARGET_VIEW_SIZE_CM,
  height: TARGET_VIEW_SIZE_CM,
};

const scoringRings = [
  { score: 5, radius: 24, fill: "#5c87c8" },
  { score: 6, radius: 20, fill: "#5c87c8" },
  { score: 7, radius: 16, fill: "#d54a3f" },
  { score: 8, radius: 12, fill: "#d54a3f" },
  { score: 9, radius: 8, fill: "#f4c54d" },
  { score: 10, radius: 4, fill: "#f4c54d" },
] as const;

const ringBoundaries = scoringRings.map((ring) => ring.radius);
const missGuideRings = Array.from(
  { length: OUTSIDE_TARGET_RING_COUNT },
  (_, index) => TARGET_RADIUS_CM + RING_WIDTH_CM * (index + 1)
);

const route = useRoute();
const arrowsApi = useArrowsApi();
const endsApi = useEndsApi();
const roundsApi = useRoundsApi();

const targetSvg = ref<SVGSVGElement | null>(null);
const arrows = ref<ArrowRecord[]>([]);
const end = ref<EndRecord | null>(null);
const round = ref<RoundRecord | null>(null);
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

function parseNumericId(value: unknown) {
  const raw = Array.isArray(value) ? value[0] : value;
  const parsed = Number(raw);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
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
  const clamped = clampPointToRadius(point, MAX_PLOTTED_RADIUS_CM);
  return {
    x: roundCoordinate(clamped.x),
    y: roundCoordinate(clamped.y),
  };
}

function getRadius(point: TargetPoint) {
  return Math.sqrt(point.x ** 2 + point.y ** 2);
}

function getScoringRadius(point: TargetPoint) {
  return Math.max(getRadius(point) - ARROW_RADIUS_CM - RING_LINE_SCORING_ALLOWANCE_CM, 0);
}

function isInnerTen(point: TargetPoint) {
  return getScoringRadius(point) <= INNER_TEN_RADIUS_CM;
}

function getScore(point: TargetPoint) {
  const radius = getScoringRadius(point);
  if (radius > SIX_RING_OUTER_RADIUS_CM) {
    return 0;
  }

  const band = Math.max(
    Math.ceil((radius - SCORING_TOLERANCE_CM) / RING_WIDTH_CM) - 1,
    0
  );
  return 10 - band;
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
  return Math.min(Math.max(value, -TARGET_VIEW_EXTENT_CM), TARGET_VIEW_EXTENT_CM - size);
}

function getActiveTargetViewBox(): ViewBox {
  if (!dragMode.value || !dragPoint.value || !dragPointerFraction.value) {
    return DEFAULT_TARGET_VIEW_BOX;
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

function getPointFromEvent(event: PointerEvent, viewBox = DEFAULT_TARGET_VIEW_BOX) {
  const pointerFraction = getPointerFractionFromEvent(event);
  if (!pointerFraction) {
    return null;
  }

  const x = viewBox.minX + pointerFraction.x * viewBox.width;
  const y = -(viewBox.minY + pointerFraction.y * viewBox.height);

  return sanitizePoint({ x, y });
}

function getDragPointFromEvent(event: PointerEvent, viewBox = DEFAULT_TARGET_VIEW_BOX) {
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
  if (arrow.score >= 9) {
    return "score-badge--gold";
  }

  if (arrow.score >= 7) {
    return "score-badge--red";
  }

  if (arrow.score >= 5) {
    return "score-badge--blue";
  }

  return "score-badge--miss";
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
  const score = getScore(point);
  if (score >= 9) {
    return "target-marker--gold";
  }

  if (score >= 7) {
    return "target-marker--red";
  }

  if (score >= 5) {
    return "target-marker--blue";
  }

  return "target-marker--miss";
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
  return isDraggedArrow(arrow) ? ARROW_RADIUS_CM : PLACED_MARKER_RADIUS_CM;
}

function getMarkerFontSize(label: string | null, isDragging = false) {
  if (!label) {
    return 0.24;
  }

  if (isDragging) {
    return label.length > 1 ? DRAG_MARKER_WIDE_FONT_SIZE_CM : DRAG_MARKER_FONT_SIZE_CM;
  }

  return PLACED_MARKER_FONT_SIZE_CM;
}

async function loadPage() {
  pending.value = true;
  errorMessage.value = "";
  end.value = null;
  round.value = null;
  arrows.value = [];
  roundEnds.value = [];

  try {
    if (!endId.value) {
      throw new Error("Invalid end id.");
    }

    const currentEnd = await endsApi.get(endId.value);
    const [currentRound, endArrows, siblingEnds] = await Promise.all([
      roundsApi.get(currentEnd.round_id),
      arrowsApi.list({ end_id: endId.value }),
      endsApi.list({ round_id: currentEnd.round_id }),
    ]);

    end.value = currentEnd;
    round.value = currentRound;
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

function startDragging(pointerId: number, pointerType: PointerEvent["pointerType"]) {
  activePointerId.value = pointerId;
  activePointerType.value = pointerType;

  if (import.meta.client) {
    window.addEventListener("pointermove", handleWindowPointerMove);
    window.addEventListener("pointerup", handleWindowPointerUp);
    window.addEventListener("pointercancel", handleWindowPointerCancel);
  }
}

function handleTargetPointerDown(event: PointerEvent) {
  if (saving.value) {
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
  startDragging(event.pointerId, event.pointerType);
}

function handleMarkerPointerDown(arrow: ArrowRecord, event: PointerEvent) {
  if (saving.value) {
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
  startDragging(event.pointerId, event.pointerType);
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

  if (!moved) {
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

onBeforeUnmount(stopDragging);

await loadPage();
</script>

<template>
  <div class="arrows-screen">
    <v-alert
      v-if="errorMessage"
      class="mb-2"
      closable
      color="error"
      variant="tonal"
      @click:close="errorMessage = ''"
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
                <div class="score-badge" :class="getScoreBadgeClass(arrow)">
                  <span class="score-order">{{ arrow.arrow_number }}</span>
                  {{ getScoreBadgeLabel(arrow) }}
                </div>
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
            <div class="drag-coordinates" :class="{ 'drag-coordinates--hidden': !dragArrowPoint }">
              <template v-if="dragArrowPoint">
                <span class="drag-coordinates__score">{{ liveDragLabel }}</span>
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
              aria-label="80 centimeter six-ring archery target face"
              @pointerdown="handleTargetPointerDown"
            >
              <circle
                v-for="ring in [...scoringRings].sort(
                  (left, right) => right.radius - left.radius
                )"
                :key="ring.score"
                cx="0"
                cy="0"
                :r="ring.radius"
                :fill="ring.fill"
              />

              <circle
                v-for="radius in ringBoundaries"
                :key="radius"
                cx="0"
                cy="0"
                :r="radius"
                fill="none"
                stroke="#1f2937"
                :stroke-width="RING_LINE_WIDTH_CM"
              />
              <circle
                cx="0"
                cy="0"
                :r="INNER_TEN_RADIUS_CM"
                fill="none"
                stroke="#1f2937"
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
                v-for="radius in missGuideRings"
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
                  },
                ]"
                :transform="`translate(${getRenderedPoint(arrow).x} ${-getRenderedPoint(
                  arrow
                ).y})`"
                @pointerdown.stop.prevent="handleMarkerPointerDown(arrow, $event)"
              >
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
  border: 0;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-family: "Avenir Next Condensed", "Gill Sans", "Trebuchet MS", sans-serif;
  font-size: 1.45rem;
  line-height: 1;
  color: #111827;
  box-shadow: 0 10px 24px rgba(17, 24, 39, 0.08);
  transition: transform 0.18s ease, box-shadow 0.18s ease, outline-color 0.18s ease;
}

.score-badge:hover {
  transform: translateY(-1px);
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

.target-marker--miss .target-marker__badge {
  fill: #d1d5db;
}

.target-marker--selected .target-marker__badge,
.target-marker--draft .target-marker__badge {
  fill: #1f5c3f;
}

.target-marker--selected .target-marker__label,
.target-marker--draft .target-marker__label {
  fill: #ffffff;
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

  .stage-nav {
    flex-wrap: wrap;
  }
}
</style>
