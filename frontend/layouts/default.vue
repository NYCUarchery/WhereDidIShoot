<template>
  <v-app>
    <div class="app-backdrop" />

    <v-main class="app-main">
      <div class="phone-shell">
        <div class="phone-status">
          <div class="status-pill" />
          <div class="brand-copy">
            <p class="eyebrow">Where Did I Shoot</p>
          </div>
        </div>

        <div class="page-shell">
          <slot />
        </div>
      </div>
    </v-main>
  </v-app>
</template>

<style scoped>
.app-backdrop {
  position: fixed;
  inset: 0;
  background:
    radial-gradient(circle at 18% 14%, rgba(125, 211, 252, 0.22), transparent 22%),
    radial-gradient(circle at 82% 8%, rgba(37, 99, 235, 0.14), transparent 18%),
    radial-gradient(circle at 50% 100%, rgba(29, 78, 216, 0.1), transparent 28%);
  pointer-events: none;
}

.app-main {
  display: flex;
  justify-content: center;
  padding: 0;
}

.phone-shell {
  width: min(100%, 414px);
  min-height: 100vh;
  padding: 0.75rem 0.75rem 1rem;
}

.phone-status {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.15rem 0.1rem 0.75rem;
}

.status-pill {
  width: 3.4rem;
  height: 0.34rem;
  border-radius: 999px;
  background: rgba(var(--wdis-ink-rgb), 0.18);
}

.brand-copy h1 {
  margin: 0;
  font-family: "Avenir Next Condensed", "Gill Sans", "Trebuchet MS", sans-serif;
  font-size: clamp(1.45rem, 5vw, 2rem);
  line-height: 1;
}

.page-shell {
  display: grid;
  gap: 0.8rem;
}

@media (min-width: 640px) {
  .app-main {
    padding: 1rem;
  }

  .phone-shell {
    min-height: calc(100vh - 2rem);
    padding: 1rem;
    border: 1px solid rgba(var(--wdis-ink-rgb), 0.08);
    border-radius: 30px;
    background: rgba(var(--wdis-surface-rgb), 0.42);
    box-shadow: 0 22px 48px rgba(var(--wdis-ink-rgb), 0.1);
    backdrop-filter: blur(12px);
  }
}
</style>
