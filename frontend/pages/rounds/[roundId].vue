<script setup lang="ts">
import type {
  ArrowRecord,
  EndRecord,
  PracticeRecord,
  RoundRecord,
  UserRecord,
} from "~/generated/sdk";
import { useDisplay } from "vuetify";

import {
  getErrorMessage,
  useArrowsApi,
  useEndsApi,
  usePracticesApi,
  useRoundsApi,
} from "~/lib/api";

const route = useRoute();
const arrowsApi = useArrowsApi();
const endsApi = useEndsApi();
const practicesApi = usePracticesApi();
const roundsApi = useRoundsApi();
const { smAndDown } = useDisplay();

const sessionUser = useCookie<UserRecord | null>("wdis-user", {
  default: () => null,
  maxAge: 60 * 60 * 24 * 30,
  sameSite: "lax",
});

if (!sessionUser.value) {
  await navigateTo("/");
}

const endSaving = ref(false);
const deletingEndId = ref<number | null>(null);
const roundNoteDialog = ref(false);
const roundNoteSaving = ref(false);
const copySaving = ref(false);
const exportSaving = ref(false);
const errorMessage = ref("");
const loadingEnds = ref(false);
const snackbar = reactive({ show: false, text: "" });

const roundNoteForm = reactive({
  notes: "",
});

const ends = ref<EndRecord[]>([]);
const selectedPractice = ref<PracticeRecord | null>(null);
const selectedRound = ref<RoundRecord | null>(null);

const practicePageLink = computed(() =>
  selectedPractice.value ? `/practices/${selectedPractice.value.id}` : "/"
);

type EndWithArrows = EndRecord & { arrows: ArrowRecord[] };

function parseRouteId(value: unknown) {
  const raw = Array.isArray(value) ? value[0] : value;
  const parsed = Number(raw);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function notify(text: string) {
  snackbar.text = text;
  snackbar.show = true;
}

async function loadPage() {
  loadingEnds.value = true;
  errorMessage.value = "";
  ends.value = [];
  selectedPractice.value = null;
  selectedRound.value = null;

  try {
    if (!sessionUser.value) {
      return;
    }

    const roundId = parseRouteId(route.params.roundId);
    if (!roundId) {
      return;
    }

    const round = await roundsApi.get(roundId);
    const practice = await practicesApi.get(round.practice_id);
    if (practice.user_id !== sessionUser.value.id) {
      throw new Error("That round is not available for the signed-in user.");
    }

    selectedPractice.value = practice;
    selectedRound.value = round;
    roundNoteForm.notes = round.notes;
    ends.value = await endsApi.list({ round_id: round.id });
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    loadingEnds.value = false;
  }
}

async function createEnd() {
  if (!selectedRound.value) {
    return;
  }

  endSaving.value = true;
  errorMessage.value = "";

  try {
    await endsApi.create({
      notes: "",
      round_id: selectedRound.value.id,
    });
    await loadPage();
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    endSaving.value = false;
  }
}

async function deleteEnd(end: EndRecord) {
  if (!import.meta.client) {
    return;
  }

  const confirmed = window.confirm(`Delete End ${end.end_number}? This also removes its arrows.`);
  if (!confirmed) {
    return;
  }

  deletingEndId.value = end.id;
  errorMessage.value = "";

  try {
    await endsApi.remove(end.id);
    notify(`End ${end.end_number} deleted.`);
    await loadPage();
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    deletingEndId.value = null;
  }
}

function openRoundNoteEditor() {
  if (!selectedRound.value) {
    return;
  }

  roundNoteForm.notes = selectedRound.value.notes;
  roundNoteDialog.value = true;
}

function closeRoundNoteDialog() {
  roundNoteDialog.value = false;
  roundNoteForm.notes = selectedRound.value?.notes ?? "";
}

async function saveRoundNote() {
  if (!selectedRound.value) {
    return;
  }

  roundNoteSaving.value = true;
  errorMessage.value = "";

  try {
    await roundsApi.update(selectedRound.value.id, {
      name: selectedRound.value.name || `Round ${selectedRound.value.id}`,
      notes: roundNoteForm.notes,
      practice_id: selectedRound.value.practice_id,
    });
    roundNoteDialog.value = false;
    await loadPage();
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    roundNoteSaving.value = false;
  }
}

function openEnd(end: EndRecord) {
  return navigateTo(`/ends/${end.id}/arrows`);
}

async function loadEndsWithArrows(roundId: number): Promise<EndWithArrows[]> {
  const roundEnds = await endsApi.list({ round_id: roundId });

  return Promise.all(
    roundEnds.map(async (end) => ({
      ...end,
      arrows: await arrowsApi.list({ end_id: end.id }),
    }))
  );
}

async function buildRoundJsonPayload() {
  if (!selectedRound.value || !selectedPractice.value || !sessionUser.value) {
    return null;
  }

  const round = selectedRound.value;
  const username = sessionUser.value.name;
  const endsWithArrows = await loadEndsWithArrows(round.id);

  return {
    username,
    practice: selectedPractice.value,
    ...round,
    ends: endsWithArrows,
  };
}

function downloadJsonFile(filename: string, content: string) {
  if (!import.meta.client) {
    throw new Error("File export is only available in a browser.");
  }

  const blob = new Blob([content], { type: "application/json;charset=utf-8" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

async function copyRoundJson() {
  copySaving.value = true;
  errorMessage.value = "";

  try {
    if (!import.meta.client || !navigator.clipboard) {
      throw new Error("Clipboard access is not available in this browser.");
    }

    const payload = await buildRoundJsonPayload();
    if (!payload) {
      return;
    }

    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    notify("Round JSON copied.");
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    copySaving.value = false;
  }
}

async function exportRoundJson() {
  exportSaving.value = true;
  errorMessage.value = "";

  try {
    const payload = await buildRoundJsonPayload();
    if (!payload) {
      return;
    }

    downloadJsonFile(`round-${payload.id}.json`, JSON.stringify(payload, null, 2));
    notify("Round JSON exported.");
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    exportSaving.value = false;
  }
}

watch(() => route.params.roundId, loadPage);

await loadPage();
</script>

<template>
  <div class="home-screen">
    <v-alert
      v-if="errorMessage"
      class="mb-4"
      closable
      color="error"
      variant="tonal"
      @click:close="errorMessage = ''"
    >
      {{ errorMessage }}
    </v-alert>

    <div class="stack">
      <div class="toolbar-row">
        <div class="toolbar-actions">
          <v-btn prepend-icon="mdi-chevron-left" :to="practicePageLink" variant="text">
            Back
          </v-btn>
        </div>
      </div>

      <section v-if="selectedRound" class="stack">
        <v-card class="context-card" rounded="xl">
          <div class="chip-row">
            <v-btn
              color="secondary"
              prepend-icon="mdi-note-edit-outline"
              size="small"
              variant="text"
              @click="openRoundNoteEditor"
            >
              Edit note
            </v-btn>
            <v-chip color="primary" size="small" variant="tonal">
              {{ selectedRound.total_score }} pts
            </v-chip>
            <v-chip color="secondary" size="small" variant="tonal">
              {{ selectedPractice?.distance_meters }} m
            </v-chip>
            <v-chip color="accent" size="small" variant="tonal">
              {{ selectedPractice?.target_face_cm }} cm face
            </v-chip>
          </div>

          <p class="page-copy mb-0">
            {{ selectedRound.notes || "No notes for this round." }}
          </p>
        </v-card>

        <div class="section-heading">
          <div>
            <p class="eyebrow">Ends</p>
          </div>
          <v-progress-circular
            v-if="loadingEnds"
            color="primary"
            indeterminate
            size="24"
          />
        </div>

        <div>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            rounded="xl"
            variant="text"
            :disabled="!selectedRound"
            :loading="endSaving"
            @click="createEnd"
          >
            New end
          </v-btn>
          <v-btn
            prepend-icon="mdi-content-copy"
            rounded="xl"
            variant="text"
            :disabled="!selectedRound"
            :loading="copySaving"
            @click="copyRoundJson"
          >
            Copy JSON
          </v-btn>
          <v-btn
            prepend-icon="mdi-download"
            rounded="xl"
            variant="text"
            :disabled="!selectedRound"
            :loading="exportSaving"
            @click="exportRoundJson"
          >
            Export JSON
          </v-btn>
        </div>

        <EmptyStateCard
          v-if="!loadingEnds && ends.length === 0"
          icon="mdi-dots-hexagon"
          text="This round does not have any ends yet."
          title="No ends yet"
        >
          <template #action>
            <v-btn
              color="primary"
              prepend-icon="mdi-plus"
              :loading="endSaving"
              @click="createEnd"
            >
              Create end
            </v-btn>
          </template>
        </EmptyStateCard>

        <div v-else class="list-stack">
          <v-card
            v-for="end in ends"
            :key="end.id"
            class="list-card"
            rounded="xl"
            @click="openEnd(end)"
          >
            <div class="list-card__top">
              <h4>End {{ end.end_number }}</h4>
              <div class="list-card__actions">
                <v-btn
                  color="error"
                  icon="mdi-delete-outline"
                  size="small"
                  variant="text"
                  :loading="deletingEndId === end.id"
                  :disabled="deletingEndId !== null && deletingEndId !== end.id"
                  :aria-label="`Delete end ${end.end_number}`"
                  @click.stop="deleteEnd(end)"
                />
                <v-icon color="primary" icon="mdi-chevron-right" />
              </div>
            </div>

            <div class="chip-row">
              <v-chip color="primary" size="small" variant="tonal">
                {{ end.total_score }} pts
              </v-chip>
            </div>

            <p class="page-copy mb-0">{{ end.notes || "No notes for this end." }}</p>
          </v-card>
        </div>
      </section>

      <EmptyStateCard
        v-else-if="!loadingEnds"
        icon="mdi-flag-remove-outline"
        text="Choose a round from the practice page to open its ends."
        title="Pick a round first"
      >
        <template #action>
          <v-btn color="primary" prepend-icon="mdi-arrow-left" to="/">
            Start from practices
          </v-btn>
        </template>
      </EmptyStateCard>
    </div>

    <v-dialog v-model="roundNoteDialog" :fullscreen="smAndDown" max-width="520">
      <v-card class="dialog-card" rounded="xl">
        <v-card-title class="pt-6 px-6">Edit round note</v-card-title>

        <v-card-text class="px-6 pb-2">
          <v-textarea
            v-model="roundNoteForm.notes"
            auto-grow
            label="Round notes"
            rows="4"
            variant="outlined"
          />
        </v-card-text>

        <v-card-actions class="px-6 pb-6">
          <v-btn variant="text" @click="closeRoundNoteDialog"> Cancel </v-btn>
          <v-spacer />
          <v-btn :loading="roundNoteSaving" color="primary" @click="saveRoundNote">
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" color="secondary">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<style scoped>
.home-screen {
  display: grid;
  gap: 0.8rem;
}

.section-heading h3,
.context-card h3,
.list-card h4 {
  margin: 0;
  font-family: "Avenir Next Condensed", "Gill Sans", "Trebuchet MS", sans-serif;
  line-height: 1;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.stack {
  display: grid;
  gap: 0.75rem;
}

.context-card,
.dialog-card,
.list-card {
  border: 1px solid rgba(var(--wdis-ink-rgb), 0.08);
  background: rgba(var(--wdis-surface-rgb), 0.94);
  box-shadow: 0 12px 24px rgba(var(--wdis-ink-rgb), 0.05);
}

.context-card {
  padding: 1rem;
}

.context-card h3,
.section-heading h3 {
  font-size: 1.45rem;
}

.toolbar-row,
.toolbar-actions,
.section-heading,
.list-card__top,
.list-card__actions,
.context-header {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.toolbar-row,
.section-heading,
.list-card__top,
.context-header {
  justify-content: space-between;
}

.context-header {
  margin-bottom: 0.55rem;
}

.toolbar-row {
  min-height: 2.1rem;
}

.toolbar-actions {
  flex: 1 1 auto;
  flex-wrap: wrap;
}

.section-heading {
  padding: 0;
}

.list-stack {
  display: grid;
  gap: 0.65rem;
}

.list-card {
  padding: 0.82rem 0.9rem;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.list-card:hover {
  transform: translateY(-1px);
  border-color: rgba(var(--wdis-primary-rgb), 0.22);
  box-shadow: 0 16px 28px rgba(var(--wdis-ink-rgb), 0.07);
}

@media (max-width: 420px) {
  .context-card,
  .dialog-card,
  .list-card {
    border-radius: 20px !important;
  }

  .toolbar-row {
    gap: 0.4rem;
  }

  .context-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
