import { defineStore } from 'pinia';

const useProductStore = defineStore('product', {
  state: () => ({
    productName: null,
    selectedCategory: null,
    aspects: {},   
  }),
  actions: {
    setProductName(name) { this.productName = name; },
    setSelectedCategory(category) { this.selectedCategory = category; },
    setAspects(aspects) { this.aspects = { ...aspects }; },
    updateAspect(key, value) { this.aspects[key] = value; },
    clear() { 
      this.productName = null; 
      this.selectedCategory = null;
      this.aspects = {}; 
    },
  },
});

export default useProductStore;
