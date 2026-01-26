import { defineStore } from 'pinia';

const useProductStore = defineStore('product', {
  state: () => ({
    marketplace: null,
    productName: null,
    selectedCategory: null,
    aspects: {},
    recommendations: [],
  }),
  actions: {
    setMarketplace(marketplace) { this.marketplace = marketplace; },
    setProductName(name) { this.productName = name; },
    setSelectedCategory(category) { this.selectedCategory = category; },
    setAspects(aspects) { this.aspects = { ...aspects }; },
    setRecommendations(recs) { this.recommendations = recs; },
    updateAspect(key, value) { this.aspects[key] = value; },
    clear() { 
      this.marketplace = null;
      this.productName = null; 
      this.selectedCategory = null;
      this.aspects = {};
      this.recommendations = [];
    },
  },
});

export default useProductStore;
