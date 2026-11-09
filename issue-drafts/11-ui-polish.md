## Summary

UI polish pass: make the whole app attractive and clean.

## Details

- One cohesive visual language: sidebar + topbar layout, card-based pages, consistent spacing scale
- Status pills with distinct colors per lifecycle state (created=gray, starting=blue pulse, running=green, stopping=amber, stopped=gray, paused=red)
- Egress mode badges (allow=green, static=amber, interactive=blue)
- Friendly empty states per page ("No workspaces yet — create one"), loading skeletons, and inline error banners carrying the daemon's one-line detail verbatim
- Monospace treatment for ids, hashes, pubkeys, sentinels; copy-to-clipboard affordances
- Light/dark theme via CSS custom properties; no external font/CDN dependencies (clean system font stack)
- Responsive enough for narrow windows (sidebar collapses)

## Notes

Attractiveness is a stated requirement of this project; this issue is the acceptance gate for the look.
