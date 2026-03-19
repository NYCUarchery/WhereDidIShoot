const dateOnlyFormatter = new Intl.DateTimeFormat('en-US', {
  dateStyle: 'medium',
  timeZone: 'UTC',
})

const dateTimeFormatter = new Intl.DateTimeFormat('en-US', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

export function formatDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  return dateOnlyFormatter.format(new Date(Date.UTC(year, month - 1, day)))
}

export function formatDateTime(value: string) {
  return dateTimeFormatter.format(new Date(value))
}
