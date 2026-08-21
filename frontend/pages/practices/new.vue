<script setup lang="ts">
import type { UserRecord } from "~/generated/sdk";
import { PracticeInputTargetFaceTypeEnum } from "~/generated/sdk";

import { getErrorMessage, usePracticesApi } from "~/lib/api";

const practicesApi = usePracticesApi();

const sessionUser = useCookie<UserRecord | null>("wdis-user", {
  default: () => null,
  maxAge: 60 * 60 * 24 * 30,
  sameSite: "lax",
});

if (!sessionUser.value) {
  await navigateTo("/");
}

interface TargetFaceOption {
  value: PracticeInputTargetFaceTypeEnum;
  title: string;
  subtitle: string;
}

const targetFaceOptions: TargetFaceOption[] = [
  {
    value: PracticeInputTargetFaceTypeEnum.compound,
    title: "Compound target",
    subtitle: "6-ring face scored 5 through 10.",
  },
  {
    value: PracticeInputTargetFaceTypeEnum.recurve,
    title: "Recurve target",
    subtitle: "Full 10-ring face scored 1 through 10.",
  },
];

const targetFaceType = ref<PracticeInputTargetFaceTypeEnum | null>(null);
const creating = ref(false);
const errorMessage = ref("");

async function createPractice() {
  if (!sessionUser.value || !targetFaceType.value || creating.value) {
    return;
  }

  creating.value = true;
  errorMessage.value = "";

  try {
    const created = await practicesApi.create({
      notes: "",
      target_face_type: targetFaceType.value,
      user_id: sessionUser.value.id,
    });
    await navigateTo(`/practices/${created.id}`);
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    creating.value = false;
  }
}
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
          <v-btn prepend-icon="mdi-chevron-left" to="/" variant="text">
            Cancel
          </v-btn>
        </div>
      </div>

      <AppPageHeader
        eyebrow="New practice"
        subtitle="Pick the target face you are shooting at. This cannot be changed once the practice is created."
        title="Choose your target face"
      />

      <v-radio-group
        v-model="targetFaceType"
        class="target-face-group"
        hide-details
        label="Target face type"
      >
        <v-radio
          v-for="option in targetFaceOptions"
          :key="option.value"
          class="target-face-option"
          :value="option.value"
        >
          <template #label>
            <div class="target-face-copy">
              <p class="target-face-title">{{ option.title }}</p>
              <p class="target-face-subtitle">{{ option.subtitle }}</p>
            </div>
          </template>
        </v-radio>
      </v-radio-group>

      <v-btn
        block
        color="primary"
        :disabled="!targetFaceType || creating"
        :loading="creating"
        rounded="xl"
        size="large"
        @click="createPractice"
      >
        Create practice
      </v-btn>
    </div>
  </div>
</template>

<style scoped>
.home-screen {
  display: grid;
  gap: 0.8rem;
}

.stack {
  display: grid;
  gap: 0.75rem;
}

.toolbar-row,
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.toolbar-row {
  justify-content: space-between;
  min-height: 2.1rem;
}

.toolbar-actions {
  flex: 1 1 auto;
  flex-wrap: wrap;
}

.target-face-copy {
  display: grid;
  gap: 0.2rem;
}

.target-face-title {
  margin: 0;
  font-family: "Avenir Next Condensed", "Gill Sans", "Trebuchet MS", sans-serif;
  font-size: 1.1rem;
  line-height: 1.15;
}

.target-face-subtitle {
  margin: 0;
  color: rgba(var(--wdis-ink-rgb), 0.68);
  font-size: 0.85rem;
  line-height: 1.4;
}

/* Vuetify puts `grid-area: control` on every .v-selection-control, which is
   inert while this container keeps its native `display: flex`. Turning the
   container into a grid makes both radios claim the same named area and stack
   them on top of each other, so only add the gap. */
:deep(.target-face-group .v-selection-control-group) {
  gap: 0.65rem;
}

:deep(.target-face-option) {
  /* Vuetify's `flex: 1 0` would make both cards share the column height. */
  flex: 0 0 auto;
  align-items: flex-start;
  border: 1px solid rgba(var(--wdis-ink-rgb), 0.12);
  border-radius: 18px;
  background: rgba(var(--wdis-surface-rgb), 0.94);
  padding: 0.85rem 1rem;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}

:deep(.target-face-option.v-selection-control--dirty) {
  border-color: rgba(var(--wdis-primary-rgb), 0.55);
  background: rgba(var(--wdis-primary-rgb), 0.08);
  box-shadow: 0 12px 24px rgba(var(--wdis-ink-rgb), 0.08);
}

:deep(.target-face-option.v-selection-control--disabled) {
  opacity: 0.6;
}

:deep(.target-face-option .v-label) {
  display: block;
  width: 100%;
  overflow: visible;
  white-space: normal;
  opacity: 1;
}

@media (max-width: 420px) {
  :deep(.target-face-option) {
    border-radius: 16px;
  }

  .toolbar-row {
    gap: 0.4rem;
  }
}
</style>
