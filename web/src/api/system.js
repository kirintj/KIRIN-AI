import user from './user'
import role from './role'
import menu from './menu'
import api from './api'
import dept from './dept'
import auditlog from './auditlog'

export default { ...user, ...role, ...menu, ...api, ...dept, ...auditlog }
