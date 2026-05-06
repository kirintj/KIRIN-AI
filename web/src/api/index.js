import auth from './auth'
import user from './user'
import role from './role'
import menu from './menu'
import api from './api'
import dept from './dept'
import auditlog from './auditlog'
import chat from './chat'
import job from './job'
import config from './config'

const system = {
  ...user,
  ...role,
  ...menu,
  ...api,
  ...dept,
  ...auditlog,
  ...config,
}

export default { ...auth, ...system, ...chat, ...job }

export { auth, user, role, menu, api, dept, auditlog, chat, job, config, system }
