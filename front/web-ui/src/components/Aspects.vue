<template>
  <div v-if="aspectKeys.length" class="aspects-section">
    <h3>✨ Product Aspects (Auto-filled)</h3>
    <p class="info-text">Review and update product specifications</p>
    <div class="aspects-grid">
      <div class="aspect-item" v-for="key in aspectKeys" :key="key">
        <label :for="key">{{ formatAspectName(key) }}</label>
        <input
          :id="key"
          type="text"
          v-model="productStore.aspects[key]"
          placeholder="Enter value"
        />
        <span v-if="productStore.aspects[key]" class="value-badge">✓ Filled</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import useProductStore from "@/storage";

const productStore = useProductStore();

const aspectKeys = computed(() => Object.keys(productStore.aspects || {}));

const formatAspectName = (key) => {
  return key
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};
</script>

<style scoped>
.aspects-section {
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.aspects-section h3 {
  margin-top: 0;
  margin-bottom: 6px;
  color: #333;
  font-size: 1rem;
}

.info-text {
  color: #777;
  font-size: 0.85rem;
  margin: 0 0 16px 0;
}

.aspects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}

.aspect-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}

.aspect-item label {
  font-weight: 500;
  font-size: 0.9rem;
  color: #333;
}

.aspect-item input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.aspect-item input:focus {
  outline: none;
  border-color: #333;
  box-shadow: 0 0 0 2px rgba(51, 51, 51, 0.1);
}

.value-badge {
  position: absolute;
  top: 6px;
  right: 8px;
  background: #e8f5e9;
  color: #2e7d32;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 3px;
}

@media (max-width: 768px) {
  .aspects-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .aspects-section {
    padding: 14px;
  }

  .aspects-grid {
    grid-template-columns: 1fr;
  }
}
</style>
