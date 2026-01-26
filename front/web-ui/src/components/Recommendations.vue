<template>
  <div v-if="recommendations.length" class="recommendations-section">
    <div class="recommendations-header">
      <h3>📊 Recommendations</h3>
    </div>

    <div class="recommendations-grid">
      <div v-for="(item, idx) in recommendations" :key="idx" class="recommendation-item">
        <div class="item-key">
          <span class="key-icon">{{ getFieldIcon(item.field) }}</span>
          <span class="key-text">{{ formatFieldName(item.field) }}</span>
        </div>
        <div class="item-value">{{ item.value }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import useProductStore from '@/storage';

const productStore = useProductStore();

const recommendations = computed(() => {
  const metadata = productStore.recommendations;
  
  if (!metadata || typeof metadata !== 'object') return [];
  
  const flattened = [];
  
  const flatten = (obj, prefix = '') => {
    Object.entries(obj).forEach(([key, val]) => {
      const fieldName = prefix ? `${prefix}.${key}` : key;
      
      if (val && typeof val === 'object' && 'value' in val) {
        const displayValue = val.unit ? `${val.value} ${val.unit}` : val.value;
        flattened.push({
          field: fieldName,
          value: displayValue,
        });
        return;
      }

      if (typeof val === 'string' || typeof val === 'number') {
        flattened.push({
          field: fieldName,
          value: String(val),
        });
        return;
      }

      if (val && typeof val === 'object' && !Array.isArray(val)) {
        flatten(val, fieldName);
      }
    });
  };
  
  flatten(metadata);
  return flattened;
});

const formatFieldName = (field) => {
  return field
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

const getFieldIcon = (field) => {
  const icons = {
    'title': '📝',
    'description': '📄',
    'category': '📂',
    'price': '💰',
    'brand': '🏷️',
    'condition': '✨',
    'quantity': '📦',
    'weight': '⚖️',
    'size': '📏',
    'color': '🎨',
    'material': '🧵',
    'manufacturer': '🏭',
  };
  return icons[field] || '✓';
};

</script>

<style scoped>
.recommendations-section {
  background: #f9fafb;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.recommendations-header {
  margin-bottom: 18px;
}

.recommendations-header h3 {
  margin: 0 0 4px 0;
  font-size: 1.1rem;
  color: #333;
  font-weight: 600;
}

.info-text {
  color: #777;
  font-size: 0.85rem;
  margin: 0;
}

.recommendations-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.recommendation-item {
  background: white;
  border: 1px solid #eee;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
}

.recommendation-item:hover {
  border-color: #ccc;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.item-key {
  background: #f5f5f5;
  border-bottom: 1px solid #eee;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  color: #333;
  min-height: 44px;
}

.key-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.key-text {
  word-break: break-word;
  line-height: 1.3;
}

.item-value {
  padding: 12px;
  font-size: 0.95rem;
  color: #333;
  flex-grow: 1;
  display: flex;
  align-items: center;
  min-height: 50px;
  word-break: break-word;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .recommendations-section {
    padding: 16px;
    margin-bottom: 18px;
  }

  .recommendations-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 10px;
  }

  .item-key {
    padding: 8px 10px;
    font-size: 0.85rem;
    min-height: 40px;
  }

  .item-value {
    padding: 10px;
    font-size: 0.9rem;
    min-height: 45px;
  }
}

@media (max-width: 480px) {
  .recommendations-grid {
    grid-template-columns: 1fr;
  }

  .item-key {
    gap: 6px;
  }

  .item-value {
    min-height: 40px;
  }
}
</style>
