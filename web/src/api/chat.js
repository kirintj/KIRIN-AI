import chatCore from './chat-core'
import knowledge from './knowledge'
import todo from './todo'
import tracker from './tracker'
import interview from './interview'
import resume from './resume'
import dashboard from './dashboard'

export default {
  ...chatCore,
  ...knowledge,
  ...todo,
  ...tracker,
  ...interview,
  ...resume,
  ...dashboard,
}
