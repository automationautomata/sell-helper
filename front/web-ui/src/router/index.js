import { createRouter, createWebHistory } from "vue-router";
import Login from "../components/Login.vue";
import Recognize from "../components/Recognize.vue";
import Aspects from "../components/Aspects.vue";
import Publish from "../components/Publish.vue";

const routes = [
  { path: "/login", component: Login },
  { path: "/recognize", component: Recognize, meta: { auth: true } },
  { path: "/aspects", component: Aspects, meta: { auth: true } },
  { path: "/publish", component: Publish, meta: { auth: true } },
  { path: "/", redirect: "/login" },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// JWT auth guard
router.beforeEach((to, _, next) => {
  const token = localStorage.getItem("token");
  if (to.meta.auth && !token) {
    next("/login");
  } else {
    next();
  }
});

export default router;
