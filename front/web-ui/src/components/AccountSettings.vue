<template>
  <div class="settings-modal" v-if="show" @click="closeModal">
    <div class="settings-content" @click.stop>
      <div class="settings-header">
        <h3>⚙️ Account Settings</h3>
        <button class="modal-close-btn" @click="closeModal">✕</button>
      </div>

      <div v-if="loading" class="loading-state">Loading settings...</div>

      <div v-else-if="error" class="error-box">
        ❌ {{ error }}
      </div>

      <div v-else-if="settingsArray.length" class="settings-grid">
        <div v-for="item in settingsArray" :key="item.name" class="setting-item">
          <div class="setting-name">{{ formatSettingName(item.name) }}</div>
          <div class="setting-values">
            <div v-for="(val, idx) in item.values" :key="idx" class="value-badge">
              {{ val }}
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        No settings available
      </div>

      <div class="modal-footer">
        <button @click="closeModal" class="btn-secondary">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

import api from '@/api';
import useProductStore from '@/storage';


const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  }
});

const emit = defineEmits(['update:modelValue']);

const productStore = useProductStore();
const loading = ref(false);
const error = ref('');
const settings = ref({});

const show = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

const settingsArray = computed(() => {
  return Object.entries(settings.value).map(([name, values]) => ({
    name,
    values: Array.isArray(values) ? values : [values]
  }));
});

const formatSettingName = (name) => {
  return name
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

const fetchSettings = () => {
  loading.value = true;
  error.value = '';
  api.get(`/settings/${productStore.marketplace}`)
    .then(response => {
      settings.value = response.data.settings || {};
    })
    .catch(err => {
      error.value = 'Failed to load settings. Please try again.';
      console.error(err);
    })
    .finally(() => {
      loading.value = false;
    });
};

const closeModal = () => {
  show.value = false;
};

const watchShow = computed(() => show.value);

watch(watchShow, (newVal) => {
  if (newVal) {
    fetchSettings();
  }
});

</script>

<style scoped>
.settings-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.settings-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  background: white;
}

.settings-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.1rem;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  padding: 20px;
}

.setting-item {
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.setting-name {
  font-weight: 600;
  color: #333;
  font-size: 0.95rem;
  border-bottom: 2px solid #e5e5e5;
  padding-bottom: 8px;
}

.setting-values {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.value-badge {
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 0.85rem;
  color: #555;
  word-break: break-word;
}

@media (max-width: 480px) {
  .settings-modal { padding: 10px; }
  .settings-content { max-height: 90vh; }
  .settings-header { padding: 16px; }
  .settings-grid { grid-template-columns: 1fr; gap: 12px; padding: 16px; }
  .setting-item { padding: 12px; }
}
</style>
