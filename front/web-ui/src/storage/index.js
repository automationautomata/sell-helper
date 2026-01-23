import { defineStore } from 'pinia';

const useProductStore = defineStore('product', {
  state: () => ({
    productName: null,
    aspects: {},   
  }),
  actions: {
    setProductName(name) { this.productName = name; },
    setAspects(aspects) { this.aspects = { ...aspects }; },
    updateAspect(key, value) { this.aspects[key] = value; },
    clear() { this.productName = null; this.aspects = {}; },
  },
});

export default useProductStore;
