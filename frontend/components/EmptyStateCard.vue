<script setup lang="ts">
withDefaults(
  defineProps<{
    icon?: string
    text: string
    title: string
  }>(),
  {
    icon: 'mdi-bullseye-arrow',
  },
)
</script>

<template>
  <v-card class="empty-state pa-6 pa-sm-7">
    <v-icon class="mb-4" color="primary" size="36">{{ icon }}</v-icon>
    <h3>{{ title }}</h3>
    <p>{{ text }}</p>
    <div class="action">
      <slot name="action" />
    </div>
  </v-card>
</template>

<style scoped>
.empty-state {
  border: 1px dashed rgba(var(--wdis-primary-rgb), 0.18);
  background: rgba(var(--wdis-surface-rgb), 0.82);
  text-align: center;
}

h3 {
  margin: 0;
  font-family: "Avenir Next Condensed", "Gill Sans", "Trebuchet MS", sans-serif;
  font-size: 1.5rem;
}

p {
  max-width: 30rem;
  margin: 0.8rem auto 0;
  color: rgba(var(--wdis-ink-rgb), 0.72);
  line-height: 1.6;
}

.action {
  margin-top: 1.15rem;
}
</style>
