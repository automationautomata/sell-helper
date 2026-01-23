<template>
  <div class="container">
    <h2>Upload Image</h2>

    <input type="file" @change="onFileChange" />
    <button @click="upload" :disabled="!file">Recognize</button>
    
    <pre v-if="result">{{ result }}</pre>
    <button v-if="result" @click="goNext">Next</button>
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
