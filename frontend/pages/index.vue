<script setup lang="ts">
import type { HealthResponse } from '~/generated/sdk'
import { useHealthApi } from '~/lib/api'

const stack = [
  { name: 'Frontend', value: 'Nuxt 3 SSR' },
  { name: 'API', value: 'Flask + Gunicorn' },
  { name: 'Database', value: 'MariaDB' },
  { name: 'Edge', value: 'Nginx reverse proxy' },
]

const healthApi = useHealthApi()

const { data, pending, error, refresh } = await useAsyncData('api-health', () =>
  healthApi.getHealth() as Promise<HealthResponse>,
)
</script>

<template>
  <main class="shell">
    <section class="hero">
      <p class="eyebrow">Modern starter</p>
      <h1>Nuxt, Flask, MariaDB, and Nginx wired into one container stack.</h1>
      <p class="lede">
        This starter gives you an SSR frontend, an API boundary, persistent
        MariaDB storage, and a single public entrypoint via Nginx.
      </p>
      <button class="refresh" type="button" @click="refresh()">
        Refresh API status
      </button>
    </section>

    <section class="grid">
      <article v-for="item in stack" :key="item.name" class="card">
        <p class="label">{{ item.name }}</p>
        <h2>{{ item.value }}</h2>
      </article>

      <article class="card status-card">
        <p class="label">Backend health</p>
        <template v-if="pending">
          <h2>Checking service status...</h2>
        </template>
        <template v-else-if="error">
          <h2>API unavailable</h2>
          <p class="muted">The frontend is up, but the backend health check failed.</p>
        </template>
        <template v-else>
          <h2>{{ data?.status === 'ok' ? 'All systems ready' : 'Needs attention' }}</h2>
          <p class="muted">
            Service: {{ data?.service }} | Database: {{ data?.database }}
          </p>
          <p class="stamp">Updated {{ data?.timestamp }}</p>
        </template>
      </article>
    </section>
  </main>
</template>

<style scoped>
.shell {
  width: min(1120px, calc(100% - 3rem));
  margin: 0 auto;
  padding: 4rem 0 5rem;
}

.hero {
  padding: 2rem 0 3rem;
}

.eyebrow {
  margin: 0 0 0.75rem;
  color: var(--accent);
  letter-spacing: 0.2em;
  text-transform: uppercase;
  font-size: 0.8rem;
  font-weight: 700;
}

h1 {
  max-width: 12ch;
  margin: 0;
  font-size: clamp(3rem, 8vw, 5.8rem);
  line-height: 0.94;
}

.lede {
  max-width: 42rem;
  margin: 1.5rem 0 0;
  color: var(--muted);
  font-size: 1.05rem;
  line-height: 1.7;
}

.refresh {
  margin-top: 1.75rem;
  padding: 0.9rem 1.3rem;
  border: 0;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--accent), var(--accent-strong));
  color: #08111f;
  cursor: pointer;
  font-weight: 700;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 1rem;
}

.card {
  min-height: 210px;
  padding: 1.4rem;
  border: 1px solid var(--panel-border);
  border-radius: 24px;
  background: var(--panel);
  box-shadow: var(--shadow);
  backdrop-filter: blur(18px);
}

.label {
  margin: 0 0 1rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.75rem;
  font-weight: 700;
}

h2 {
  margin: 0;
  font-size: 1.5rem;
  line-height: 1.2;
}

.muted,
.stamp {
  color: var(--muted);
  line-height: 1.6;
}

.stamp {
  margin-top: 1rem;
}

.status-card {
  grid-column: span 2;
}

@media (max-width: 700px) {
  .shell {
    width: min(100% - 1.5rem, 1120px);
    padding-top: 2rem;
  }

  .status-card {
    grid-column: auto;
  }
}
</style>
