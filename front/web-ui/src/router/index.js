import { createRouter, createWebHistory } from "vue-router";
import Login from "@/components/Login.vue";
import Marketplace from "@/components/Marketplace.vue";
import Recognize from "@/components/Recognize.vue";
import Publish from "@/components/Publish.vue";

const routes = [
  { path: "/", component: Login },
  { path: "/marketplace", component: Marketplace },
  { path: "/recognize", component: Recognize },
  { path: "/publish", component: Publish },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
