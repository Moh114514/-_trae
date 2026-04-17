import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const buildings = ref([])
  const meters = ref([])
  const dateRange = ref({})
  const dataSummary = ref({})
  const loading = ref(false)

  const setBuildings = (data) => {
    buildings.value = data
  }

  const setMeters = (data) => {
    meters.value = data
  }

  const setDateRange = (data) => {
    dateRange.value = data
  }

  const setDataSummary = (data) => {
    dataSummary.value = data
  }

  const setLoading = (status) => {
    loading.value = status
  }

  return {
    buildings,
    meters,
    dateRange,
    dataSummary,
    loading,
    setBuildings,
    setMeters,
    setDateRange,
    setDataSummary,
    setLoading
  }
})
