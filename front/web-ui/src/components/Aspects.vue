<template>
  <div class="container">
    <h2>Product Aspects</h2>
    
    <input v-model="category" placeholder="Category" />
    <button @click="loadAspects">Load Aspects</button>

    <pre v-if="data">{{ data }}</pre>
    <button v-if="data" @click="goNext">Next</button>
  </div>

</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api/api';
import { useProductStore } from '../stores/product';

const marketplace = ref('ozon');
const category = ref('');
const data = ref(null);
const router = useRouter();
const productStore = useProductStore();

const loadAspects = () => {
  api.post(`/product/${marketplace.value}/aspects`, {
    product_name: productStore.productName,
    category: category.value,
  })
  .then((res) => {
    data.value = res.data;
    productStore.setAspects(res.data.product.aspects); // in-memory only
  })
  .catch(() => alert('Failed to load aspects'));
};

const goNext = () => router.push('/publish');
</script>

