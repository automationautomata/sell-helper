<template>
  <div class="container marketplace-card">
    <div class="marketplace-header">
      <h2>Select Marketplace</h2>
      <p class="subtitle">Choose which marketplace to publish on</p>
    </div>

    <div class="marketplaces-grid">
      <div
        v-for="mp in marketplaces"
        :key="mp.id"
        @click="selectMarketplace(mp.id)"
        :class="['marketplace-item', { selected: selectedMarketplace === mp.id }]"
      >
        <div class="marketplace-icon">{{ mp.icon }}</div>
        <span class="marketplace-name">{{ mp.name }}</span>
        <span v-if="selectedMarketplace === mp.id" class="check-mark">✓</span>
      </div>
    </div>

    <button 
      @click="login" 
      :disabled="!selectedMarketplace"
      class="btn-proceed"
    >
      Login and Continue
    </button>

  </div>
</template>

<script setup>
import { ref } from 'vue';
import useProductStore from '@/storage';
import api from '@/api';

const productStore = useProductStore();
const selectedMarketplace = ref('');
const isLoggingIn = ref(false);

const marketplaces = [
  {
    id: 'ozon',
    name: 'Ozon',
    icon: '🛒',
  },
  {
    id: 'ebay',
    name: 'eBay',
    icon: '🛒',
  },
  {
    id: 'aliexpress',
    name: 'AliExpress',
    icon: '🛒',
  }
];

const selectMarketplace = (id) => {
  selectedMarketplace.value = id;
};

const login = () => {
  if (!selectedMarketplace.value) return;
  
  isLoggingIn.value = true;
  productStore.setMarketplace(selectedMarketplace.value);
  
  api.get(`/login/${selectedMarketplace.value}`)
    .then(() => {
      window.open(url);
      router.push("/recognize");
    })
  
};
</script>

<style scoped>
.marketplace-card {
  max-width: 700px;
}

.marketplace-header h2 {
  font-size: 1.6rem;
}

.marketplaces-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.marketplace-item {
  padding: 24px 16px;
  position: relative;
  text-align: center;
}

.marketplace-item:hover {
  border-color: #999;
  background: #f5f5f5;
}

.marketplace-item.selected {
  background: #f0f0f0;
  border-color: #333;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1);
}

.marketplace-icon {
  font-size: 2.5rem;
}

.marketplace-name {
  font-weight: 600;
  color: #333;
  font-size: 1rem;
}

.btn-proceed {
  padding: 12px 24px;
  font-size: 0.95rem;
}


@media (max-width: 768px) {
  .marketplace-card {
    max-width: 100%;
  }

  .marketplaces-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 24px;
  }

  .marketplace-item {
    padding: 18px 12px;
  }

  .marketplace-icon {
    font-size: 2rem;
  }

  .marketplace-header h2 {
    font-size: 1.3rem;
  }
}

@media (max-width: 480px) {
  .marketplaces-grid {
    grid-template-columns: 1fr;
  }

  .marketplace-item {
    padding: 16px 12px;
  }

  .marketplace-name {
    font-size: 0.95rem;
  }
}
</style>
