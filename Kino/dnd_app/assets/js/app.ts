// We import the CSS which is extracted to its own file by the bundler
import "../css/app.css"

// If you want to use Phoenix channels, run `mix help phx.gen.channel`
// to get started, and then uncomment the line below.
// import "./user_socket.js"

// You can include dependencies in two ways.
// 1. npm package dependency:
//    See https://npmjs.com for packages with "phoenix" in the name, like "phoenix_html"
//
// 2. If you have JS assets to add, uncomment the following:
// import "./custom.js"

// Include phoenix_html to handle method=PUT/DELETE in forms and buttons.
import "phoenix_html"

// Establish Phoenix Socket and LiveView configuration.
import { Socket } from "phoenix"
import { LiveSocket } from "phoenix_live_view"
import { initLiveReact } from "phoenix_live_react"

// Show progress bar on live navigation and form submits
import topbar from "topbar"

// Get CSRF token from meta tag
const csrfTokenElement = document.querySelector("meta[name='csrf-token']")
if (!csrfTokenElement) {
  console.error("CSRF token meta tag not found")
}

const csrfToken = csrfTokenElement?.getAttribute("content") || ""

// Initialize Phoenix Live React
initLiveReact()

// Set up window.Components namespace for React components
;(window as any).Components = (window as any).Components || {}

// Import React components
import './components/DiceRoller'

const liveSocket = new LiveSocket("/live", Socket, {
  params: { _csrf_token: csrfToken }
})

// Configure topbar
topbar.config({ barColors: { 0: "#29d" }, shadowColor: "rgba(0, 0, 0, .3)" })

window.addEventListener("phx:page-loading-start", () => topbar.show())
window.addEventListener("phx:page-loading-stop", () => topbar.hide())

// Connect if there are any LiveViews on the page
liveSocket.connect()

// Expose liveSocket on window for web console debug logs and latency simulation:
// >> liveSocket.enableDebug()
// >> liveSocket.enableLatencySim(1000)  // enabled for duration of browser session
// >> liveSocket.disableLatencySim()
;(window as any).liveSocket = liveSocket

