<script setup lang="ts">
import type { PracticeRecord, UserRecord } from "~/generated/sdk";

import { getErrorMessage, useAuthApi, usePracticesApi } from "~/lib/api";
import { formatDateTime } from "~/lib/format";

const authApi = useAuthApi();
const practicesApi = usePracticesApi();

const sessionUser = useCookie<UserRecord | null>("wdis-user", {
  default: () => null,
  maxAge: 60 * 60 * 24 * 30,
  sameSite: "lax",
});

const loginPending = ref(false);
const deletingPracticeId = ref<number | null>(null);
const errorMessage = ref("");
const snackbar = reactive({ show: false, text: "" });
const loadingPractices = ref(false);

const loginForm = reactive({
  password: "",
  username: sessionUser.value?.name ?? "",
});

const practices = ref<PracticeRecord[]>([]);

function notify(text: string) {
  snackbar.text = text;
  snackbar.show = true;
}

async function loadPractices() {
  if (!sessionUser.value) {
    practices.value = [];
    return;
  }

  loadingPractices.value = true;
  errorMessage.value = "";

  try {
    practices.value = await practicesApi.list({ user_id: sessionUser.value.id });
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    loadingPractices.value = false;
  }
}

async function signIn() {
  loginPending.value = true;
  errorMessage.value = "";

  try {
    const response = await authApi.login(loginForm);
    sessionUser.value = response.user;
    loginForm.username = response.user.name;
    loginForm.password = "";
    await loadPractices();

    if (response.created) {
      notify(`Registered ${response.user.name}.`);
      return;
    }

    if (response.password_initialized) {
      notify("Password saved for this existing user.");
      return;
    }

    notify(`Welcome back, ${response.user.name}.`);
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    loginPending.value = false;
  }
}

async function deletePractice(practice: PracticeRecord) {
  if (deletingPracticeId.value) {
    return;
  }

  if (import.meta.client) {
    const confirmed = window.confirm("Delete this practice and all of its rounds and arrows?");
    if (!confirmed) {
      return;
    }
  }

  deletingPracticeId.value = practice.id;
  errorMessage.value = "";

  try {
    await practicesApi.remove(practice.id);
    await loadPractices();
    notify("Practice deleted.");
  } catch (error) {
    errorMessage.value = getErrorMessage(error);
  } finally {
    deletingPracticeId.value = null;
  }
}

function openPractice(practice: PracticeRecord) {
  if (deletingPracticeId.value !== null) {
    return;
  }

  return navigateTo(`/practices/${practice.id}`);
}

function signOut() {
  sessionUser.value = null;
  loginForm.password = "";
  errorMessage.value = "";
  practices.value = [];
}

if (sessionUser.value) {
  await loadPractices();
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

    <div v-if="!sessionUser" class="stack">
      <v-card class="auth-card" rounded="xl">
        <div class="auth-copy">
          <p class="eyebrow">Login</p>
          <p class="page-copy mb-0">
            輸入密碼就會自動註冊新帳號，或登入既有帳號。
            請不要使用在其他地方使用的密碼。這個應用程式不能很好的保護你的資料安全。
          </p>
        </div>

        <v-text-field
          v-model="loginForm.username"
          autocomplete="username"
          density="comfortable"
          label="Username"
          prepend-inner-icon="mdi-account-outline"
          variant="outlined"
        />

        <v-text-field
          v-model="loginForm.password"
          autocomplete="current-password"
          density="comfortable"
          label="Password"
          prepend-inner-icon="mdi-lock-outline"
          type="password"
          variant="outlined"
          @keydown.enter.prevent="signIn"
        />

        <v-btn
          block
          color="primary"
          :loading="loginPending"
          rounded="xl"
          size="large"
          @click="signIn"
        >
          Continue
        </v-btn>
      </v-card>
    </div>

    <div v-else class="stack">
      <v-card class="session-card" rounded="xl">
        <div class="session-row">
          <h3>{{ sessionUser.name }}</h3>

          <v-btn
            class="logout-button"
            color="secondary"
            icon="mdi-logout"
            size="small"
            variant="tonal"
            @click="signOut"
          />
        </div>
      </v-card>

      <div class="toolbar-row">
        <div class="toolbar-actions">
          <v-btn
            color="primary"
            prepend-icon="mdi-calendar-plus"
            rounded="xl"
            variant="text"
            to="/practices/new"
          >
            New practice
          </v-btn>
        </div>
      </div>

      <section class="stack">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Practices</p>
          </div>
          <v-progress-circular
            v-if="loadingPractices"
            color="primary"
            indeterminate
            size="24"
          />
        </div>

        <EmptyStateCard
          v-if="!loadingPractices && practices.length === 0"
          icon="mdi-calendar-blank-outline"
          text="This user does not have any practice sessions yet."
          title="No practices yet"
        >
          <template #action>
            <v-btn
              color="primary"
              prepend-icon="mdi-calendar-plus"
              to="/practices/new"
            >
              Create practice
            </v-btn>
          </template>
        </EmptyStateCard>

        <div v-else class="list-stack">
          <v-card
            v-for="practice in practices"
            :key="practice.id"
            class="list-card"
            rounded="xl"
            :class="{ 'list-card--disabled': deletingPracticeId !== null }"
            @click="openPractice(practice)"
          >
            <div class="list-card__top">
              <div>
                <p class="list-label">Practice</p>
              </div>
              <div class="list-card__actions">
                <v-btn
                  color="error"
                  icon="mdi-delete-outline"
                  size="small"
                  variant="text"
                  aria-label="Delete practice"
                  :loading="deletingPracticeId === practice.id"
                  :disabled="deletingPracticeId !== null"
                  @click.stop="deletePractice(practice)"
                />
                <v-icon color="primary" icon="mdi-chevron-right" />
              </div>
            </div>

            <div class="chip-row">
              <v-chip color="secondary" size="small" variant="tonal">
                {{ formatDateTime(practice.created_at) }}
              </v-chip>
            </div>

            <p class="page-copy mb-0">
              {{ practice.notes || "No notes for this practice." }}
            </p>
          </v-card>
        </div>
      </section>
    </div>

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

.auth-copy h3,
.session-card h3,
.section-heading h3,
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

.auth-card,
.session-card,
.list-card {
  border: 1px solid rgba(var(--wdis-ink-rgb), 0.08);
  background: rgba(var(--wdis-surface-rgb), 0.94);
  box-shadow: 0 12px 24px rgba(var(--wdis-ink-rgb), 0.05);
}

.auth-card,
.session-card {
  padding: 1rem;
}

.auth-card {
  display: grid;
  gap: 0.8rem;
}

.session-card {
  padding: 0.58rem 0.8rem;
}

.auth-copy {
  display: grid;
  gap: 0.25rem;
}

.auth-copy h3,
.section-heading h3 {
  font-size: 1.45rem;
}

.session-card h3 {
  font-size: 1rem;
  font-weight: 500;
  letter-spacing: 0.01em;
}

.session-row,
.toolbar-row,
.toolbar-actions,
.section-heading,
.list-card__top,
.list-card__actions {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.session-row,
.toolbar-row,
.section-heading,
.list-card__top {
  justify-content: space-between;
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

.list-card--disabled {
  cursor: progress;
  opacity: 0.75;
}

.list-label {
  margin: 0;
  color: rgba(var(--wdis-ink-rgb), 0.52);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.logout-button {
  min-width: 2rem;
  width: 2rem;
  height: 2rem;
}

.logout-button :deep(.v-icon) {
  font-size: 1rem;
}

@media (max-width: 420px) {
  .auth-card,
  .session-card,
  .list-card {
    border-radius: 20px !important;
  }

  .toolbar-row {
    gap: 0.4rem;
  }
}
</style>
