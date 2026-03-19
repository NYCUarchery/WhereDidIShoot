<script setup lang="ts">
defineProps<{
  eyebrow?: string
  subtitle: string
  title: string
}>()
</script>

<template>
  <div class="page-header">
    <div class="copy">
      <p v-if="eyebrow" class="eyebrow">{{ eyebrow }}</p>
      <h2 class="title">{{ title }}</h2>
      <p class="subtitle">{{ subtitle }}</p>
    </div>

    <div class="actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: grid;
  gap: 1rem;
  align-items: end;
  margin-bottom: 1.4rem;
}

.title {
  margin: 0;
  font-family: "Avenir Next Condensed", "Gill Sans", "Trebuchet MS", sans-serif;
  font-size: clamp(2rem, 10vw, 3.4rem);
  line-height: 0.98;
}

.subtitle {
  max-width: 42rem;
  margin: 0.6rem 0 0;
  color: rgba(var(--wdis-ink-rgb), 0.72);
  line-height: 1.65;
}

.actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

@media (min-width: 720px) {
  .page-header {
    grid-template-columns: minmax(0, 1fr) auto;
  }
}
</style>
