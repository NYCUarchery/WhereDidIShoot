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
import { formatDateTime } from "~/lib/format";

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

const practiceNoteDialog = ref(false);
const practiceNoteSaving = ref(false);
const roundSaving = ref(false);
const copySaving = ref(false);
const exportSaving = ref(false);
const deletingRoundId = ref<number | null>(null);
const errorMessage = ref("");
const loadingRounds = ref(false);
const snackbar = reactive({ show: false, text: "" });

const practiceNoteForm = reactive({
  notes: "",
});

const rounds = ref<RoundRecord[]>([]);
const selectedPractice = ref<PracticeRecord | null>(null);

type EndWithArrows = EndRecord & { arrows: ArrowRecord[] };
type RoundWithChildren = RoundRecord & { ends: EndWithArrows[] };

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
  loadingRounds.value = true;
  errorMessage.value = "";
  rounds.value = [];
  selectedPractice.value = null;

  try {
    if (!sessionUser.value) {
      return;
    }

    const practiceId = parseRouteId(route.params.practiceId);
    if (!practiceId) {
      return;
    }

    const practice = await practicesApi.get(practiceId);
    if (practice.user_id !== sessionUser.value.id) {
      throw new Error("That practice is not available for the signed-in user.");
    }

    selectedPractice.value = practice;
    practiceNoteForm.notes = practice.notes;
    rounds.value = await roundsApi.list({ practice_id: practice.id });
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    loadingRounds.value = false;
  }
}

async function createRound() {
  if (!selectedPractice.value) {
    return;
  }

  roundSaving.value = true;
  errorMessage.value = "";

  try {
    const round = await roundsApi.create({
      name: `Round ${rounds.value.length + 1}`,
      notes: "",
      practice_id: selectedPractice.value.id,
    });
    const end = await endsApi.create({
      notes: "",
      round_id: round.id,
    });
    await navigateTo(`/ends/${end.id}`);
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    roundSaving.value = false;
  }
}

function openPracticeNoteEditor() {
  if (!selectedPractice.value) {
    return;
  }

  practiceNoteForm.notes = selectedPractice.value.notes;
  practiceNoteDialog.value = true;
}

function closePracticeNoteDialog() {
  practiceNoteDialog.value = false;
  practiceNoteForm.notes = selectedPractice.value?.notes ?? "";
}

async function savePracticeNote() {
  if (!selectedPractice.value) {
    return;
  }

  practiceNoteSaving.value = true;
  errorMessage.value = "";

  try {
    await practicesApi.update(selectedPractice.value.id, {
      notes: practiceNoteForm.notes,
      user_id: selectedPractice.value.user_id,
    });
    practiceNoteDialog.value = false;
    await loadPage();
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    practiceNoteSaving.value = false;
  }
}

function openRound(round: RoundRecord) {
  return navigateTo(`/rounds/${round.id}`);
}

async function deleteRound(round: RoundRecord) {
  if (deletingRoundId.value !== null) {
    return;
  }

  if (
    import.meta.client &&
    !window.confirm(`Delete Round ${round.round_order} and all of its ends and arrows?`)
  ) {
    return;
  }

  deletingRoundId.value = round.id;
  errorMessage.value = "";

  try {
    await roundsApi.remove(round.id);
    await loadPage();
    notify(`Round ${round.round_order} deleted.`);
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    deletingRoundId.value = null;
  }
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

async function buildPracticeJsonPayload() {
  if (!selectedPractice.value || !sessionUser.value) {
    return null;
  }

  const practice = selectedPractice.value;
  const username = sessionUser.value.name;
  const roundsWithChildren: RoundWithChildren[] = await Promise.all(
    rounds.value.map(async (round) => ({
      ...round,
      ends: await loadEndsWithArrows(round.id),
    }))
  );

  return {
    username,
    ...practice,
    rounds: roundsWithChildren,
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

async function copyPracticeJson() {
  copySaving.value = true;
  errorMessage.value = "";

  try {
    if (!import.meta.client || !navigator.clipboard) {
      throw new Error("Clipboard access is not available in this browser.");
    }

    const payload = await buildPracticeJsonPayload();
    if (!payload) {
      return;
    }

    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    notify("Practice JSON copied.");
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    copySaving.value = false;
  }
}

async function exportPracticeJson() {
  exportSaving.value = true;
  errorMessage.value = "";

  try {
    const payload = await buildPracticeJsonPayload();
    if (!payload) {
      return;
    }

    downloadJsonFile(`practice-${payload.id}.json`, JSON.stringify(payload, null, 2));
    notify("Practice JSON exported.");
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    exportSaving.value = false;
  }
}

watch(() => route.params.practiceId, loadPage);

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
          <v-btn prepend-icon="mdi-chevron-left" to="/" variant="text"> Back </v-btn>
        </div>
      </div>

      <section v-if="selectedPractice" class="stack">
        <v-card class="context-card" rounded="xl">
          <div class="context-header">
            <div>Practice: {{ formatDateTime(selectedPractice.created_at) }}</div>
            <v-btn
              color="secondary"
              prepend-icon="mdi-note-edit-outline"
              size="small"
              variant="text"
              @click="openPracticeNoteEditor"
            >
              Edit note
            </v-btn>
          </div>

          <div class="chip-row mb-3">
            <v-chip color="secondary" size="small" variant="tonal">
              {{ selectedPractice.distance_meters }} m
            </v-chip>
            <v-chip color="accent" size="small" variant="tonal">
              {{ selectedPractice.target_face_cm }} cm face
            </v-chip>
          </div>

          <p class="page-copy mb-0">
            {{ selectedPractice.notes || "No notes for this practice." }}
          </p>
        </v-card>

        <div class="section-heading">
          <v-progress-circular
            v-if="loadingRounds"
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
            :disabled="!selectedPractice"
            :loading="roundSaving"
            @click="createRound"
          >
            New round
          </v-btn>
          <v-btn
            prepend-icon="mdi-content-copy"
            rounded="xl"
            variant="text"
            :disabled="!selectedPractice"
            :loading="copySaving"
            @click="copyPracticeJson"
          >
            Copy JSON
          </v-btn>
          <v-btn
            prepend-icon="mdi-download"
            rounded="xl"
            variant="text"
            :disabled="!selectedPractice"
            :loading="exportSaving"
            @click="exportPracticeJson"
          >
            Export JSON
          </v-btn>
        </div>

        <EmptyStateCard
          v-if="!loadingRounds && rounds.length === 0"
          icon="mdi-flag-outline"
          text="This practice does not have any rounds yet."
          title="No rounds yet"
        >
          <template #action>
            <v-btn
              color="primary"
              prepend-icon="mdi-plus"
              :loading="roundSaving"
              @click="createRound"
            >
              Create round
            </v-btn>
          </template>
        </EmptyStateCard>

        <div v-else class="list-stack">
          <v-card
            v-for="round in rounds"
            :key="round.id"
            class="list-card"
            rounded="xl"
            @click="openRound(round)"
          >
            <div class="list-card__top">
              <h4>Round {{ round.round_order }}</h4>
              <div class="list-card__actions">
                <v-btn
                  color="error"
                  density="comfortable"
                  icon="mdi-delete-outline"
                  variant="text"
                  :aria-label="`Delete round ${round.round_order}`"
                  :disabled="deletingRoundId !== null && deletingRoundId !== round.id"
                  :loading="deletingRoundId === round.id"
                  @click.stop="deleteRound(round)"
                />
                <v-icon color="primary" icon="mdi-chevron-right" />
              </div>
            </div>

            <div class="chip-row">
              <v-chip color="primary" size="small" variant="tonal">
                {{ round.total_score }} pts
              </v-chip>
              <v-chip color="secondary" size="small" variant="tonal">
                {{ selectedPractice.distance_meters }} m
              </v-chip>
              <v-chip color="accent" size="small" variant="tonal">
                {{ selectedPractice.target_face_cm }} cm face
              </v-chip>
            </div>

            <p class="page-copy mb-0">{{ round.notes || "No notes for this round." }}</p>
          </v-card>
        </div>
      </section>

      <EmptyStateCard
        v-else-if="!loadingRounds"
        icon="mdi-calendar-remove-outline"
        text="Choose a practice from the home page to open its rounds."
        title="Pick a practice first"
      >
        <template #action>
          <v-btn color="primary" prepend-icon="mdi-arrow-left" to="/">
            Go to practices
          </v-btn>
        </template>
      </EmptyStateCard>
    </div>

    <v-dialog v-model="practiceNoteDialog" :fullscreen="smAndDown" max-width="520">
      <v-card class="dialog-card" rounded="xl">
        <v-card-title class="pt-6 px-6">Edit practice note</v-card-title>

        <v-card-text class="px-6 pb-2">
          <v-textarea
            v-model="practiceNoteForm.notes"
            auto-grow
            label="Practice notes"
            rows="4"
            variant="outlined"
          />
        </v-card-text>

        <v-card-actions class="px-6 pb-6">
          <v-btn variant="text" @click="closePracticeNoteDialog"> Cancel </v-btn>
          <v-spacer />
          <v-btn :loading="practiceNoteSaving" color="primary" @click="savePracticeNote">
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
.context-header,
.list-card__actions {
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

.list-label {
  margin: 0;
  color: rgba(var(--wdis-ink-rgb), 0.52);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
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
