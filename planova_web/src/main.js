import './assets/main.css';
import 'bootstrap/dist/css/bootstrap.css';
import 'vue-awesome-paginate/dist/style.css';

import { createApp } from 'vue';
import { createPinia } from 'pinia';
import VueAwesomePaginate from 'vue-awesome-paginate';

import App from './App.vue';
import router from './router';
import VCalendar from 'v-calendar';

const app = createApp(App);
const pinia = createPinia()

app.use(VueAwesomePaginate);
app.use(pinia);
app.use(router);
app.use(VCalendar, {}); 

app.mount('#app');
