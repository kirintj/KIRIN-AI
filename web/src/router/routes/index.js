import i18n from '~/i18n'
const { t } = i18n.global

const Layout = () => import('@/layout/index.vue')

export const basicRoutes = [
  {
    path: '/',
    redirect: '/workbench',
    meta: { order: 0 },
  },
  {
    name: t('views.workbench.label_workbench'),
    path: '/workbench',
    component: Layout,
    children: [
      {
        path: '',
        component: () => import('@/views/workbench/index.vue'),
        name: `${t('views.workbench.label_workbench')}Default`,
        meta: {
          title: t('views.workbench.label_workbench'),
          icon: 'icon-park-outline:workbench',
          affix: true,
        },
      },
    ],
    meta: { order: 1 },
  },
  {
    name: 'Agent智能对话',
    path: '/agent-chat',
    component: Layout,
    children: [
      {
        path: '',
        component: () => import('@/views/agent-chat/index.vue'),
        name: 'AgentChatDefault',
        meta: {
          title: 'Agent智能对话',
          icon: 'icon-park-outline:topic',
        },
      },
    ],
    meta: { order: 2 },
  },
  {
    name: '知识库管理',
    path: '/knowledge',
    component: Layout,
    children: [
      {
        path: '',
        component: () => import('@/views/knowledge/index.vue'),
        name: 'KnowledgeDefault',
        meta: {
          title: '知识库管理',
          icon: 'icon-park-outline:data',
        },
      },
    ],
    meta: { order: 3 },
  },
  {
    name: '待办任务',
    path: '/todo',
    component: Layout,
    children: [
      {
        path: '',
        component: () => import('@/views/todo/index.vue'),
        name: 'TodoDefault',
        meta: {
          title: '待办任务',
          icon: 'icon-park-outline:table-report',
        },
      },
    ],
    meta: { order: 4 },
  },
  {
    name: '求职进度',
    path: '/tracker',
    component: Layout,
    children: [
      {
        path: '',
        component: () => import('@/views/tracker/index.vue'),
        name: 'TrackerDefault',
        meta: {
          title: '求职进度',
          icon: 'icon-park-outline:torch',
        },
      },
    ],
    meta: { order: 5 },
  },
  {
    name: '面试模拟',
    path: '/interview-sim',
    component: Layout,
    children: [
      {
        path: '',
        component: () => import('@/views/interview-sim/index.vue'),
        name: 'InterviewSimDefault',
        meta: {
          title: '面试模拟',
          icon: 'icon-park-outline:hourglass-full',
        },
      },
    ],
    meta: { order: 6 },
  },
  {
    name: t('views.profile.label_profile'),
    path: '/profile',
    component: Layout,
    isHidden: true,
    children: [
      {
        path: '',
        component: () => import('@/views/profile/index.vue'),
        name: `${t('views.profile.label_profile')}Default`,
        meta: {
          title: t('views.profile.label_profile'),
          icon: 'user',
          affix: true,
        },
      },
    ],
    meta: { order: 99 },
  },
  {
    name: '403',
    path: '/403',
    component: () => import('@/views/error-page/403.vue'),
    isHidden: true,
  },
  {
    name: '404',
    path: '/404',
    component: () => import('@/views/error-page/404.vue'),
    isHidden: true,
  },
  {
    name: 'Login',
    path: '/login',
    component: () => import('@/views/login/index.vue'),
    isHidden: true,
    meta: {
      title: '登录页',
    },
  },
]

export const NOT_FOUND_ROUTE = {
  name: 'NotFound',
  path: '/:pathMatch(.*)*',
  redirect: '/404',
  isHidden: true,
}

export const EMPTY_ROUTE = {
  name: 'Empty',
  path: '/:pathMatch(.*)*',
  component: null,
}

const modules = import.meta.glob('@/views/**/route.js', { eager: true })
const asyncRoutes = []
Object.keys(modules).forEach((key) => {
  asyncRoutes.push(modules[key].default)
})

// 加载 views 下每个模块的 index.vue 文件
const vueModules = import.meta.glob('@/views/**/index.vue')

export { asyncRoutes, vueModules }
