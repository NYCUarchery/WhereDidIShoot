<script setup lang="ts">
const route = useRoute()

const rawEndId = Array.isArray(route.params.endId) ? route.params.endId[0] : route.params.endId

if (rawEndId) {
  await navigateTo(`/ends/${rawEndId}/arrows`, { replace: true })
} else {
  await navigateTo('/', { replace: true })
}
</script>
