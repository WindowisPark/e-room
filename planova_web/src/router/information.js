export default [
  {
    path: '/information/planet',
    name: 'information/planet',
    component: () => import('../pages/information/InformationPage.vue'),
  },
  {
    
    path: '/information/partnership',
    name: 'information/partnership',
    component: () => import('../pages/information/PartnershipPage.vue'),
  },
];
