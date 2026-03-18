import { Configuration, HealthApi } from '~/generated/sdk'

function createApiConfiguration() {
  const config = useRuntimeConfig()
  const basePath = import.meta.server
    ? config.apiInternalBase
    : config.public.apiBase

  return new Configuration({ basePath })
}

export function useHealthApi() {
  return new HealthApi(createApiConfiguration())
}
