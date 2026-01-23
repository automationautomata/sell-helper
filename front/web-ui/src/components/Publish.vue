<template>
  <div class="container">
    <h2>Publish Product</h2>

    <input v-model="title" placeholder="Title" required />
    <input v-model="category" placeholder="Category" required />
    <textarea v-model="description" placeholder="Description" required></textarea>
    <input type="number" v-model.number="price" placeholder="Price" min="0" required />
    
    <select v-model="currency" required>
      <option value="USD">USD</option>
      <option value="RUB">RUB</option>
      <option value="EUR">EUR</option>
    </select>
    
    <select v-model="country" required>
      <option value="RU">Russia</option>
      <option value="US">USA</option>
      <option value="DE">Germany</option>
    </select>
    
    <input type="number" v-model.number="quantity" placeholder="Quantity" min="1" required />

    <div v-if="aspectKeys.length">
      <h3>Product Aspects</h3>
      <div v-for="key in aspectKeys" :key="key" class="aspect-item">
        <label :for="key">{{ key }}</label>
        <input
          :id="key"
          type="text"
          v-model="productStore.aspects[key]"
          placeholder="Enter value"
        />
      </div>
    </div>

    <input type="file" @change="onFileChange" required />

    <button @click="publish" :disabled="!canPublish">Publish</button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import api from '@/api';
import useProductStore from '@/storage';

const title = ref('');
const category = ref('');
const description = ref('');
const price = ref(null);
const currency = ref('USD');
const country = ref('RU');
const quantity = ref(1);
const file = ref(null);

const productStore = useProductStore();

const aspectKeys = computed(() => Object.keys(productStore.aspects || {}));

const canPublish = computed(() => {
  return (
    title.value &&
    description.value &&
    category.value &&
    price.value > 0 &&
    quantity.value > 0 &&
    file.value
  );
});

const onFileChange = (e) => {
  file.value = e.target.files[0];
};

const publish = () => {
  if (!canPublish.value) return;

  const item = {
    title: title.value,
    description: description.value,
    category: category.value,
    price: price.value,
    currency: currency.value,
    country: country.value,
    quantity: quantity.value,
    product: productStore.aspects, 
    marketplace_aspects: {},
  };

  const formData = new FormData();
  formData.append('item', JSON.stringify(item));
  formData.append('images', file.value);

  api.post('/product/ozon/publish', formData)
    .then(() => {
      alert('Product published successfully!');
      title.value = '';
      description.value = '';
      category.value = '';
      price.value = null;
      quantity.value = 1;
      file.value = null;
      productStore.clear();
    })
    .catch(() => alert('Publish failed'));
};
</script>
