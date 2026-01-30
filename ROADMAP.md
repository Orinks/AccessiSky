# AccessiSky Roadmap

A focused roadmap for AccessiSky - the accessible sky tracking companion to AccessiWeather.

## Vision

AccessiSky helps users know **what's happening in the sky** and **when to look up**. The app answers:
- "Can I see the ISS tonight?"
- "When is the next meteor shower?"
- "Is tonight good for stargazing?"
- "What planets are visible?"

## Core Principles

1. **Accessibility First** - Every feature must work with screen readers
2. **API Over Calculation** - Use free APIs instead of local math where possible
3. **Actionable Information** - Tell users *when* to go outside and *what* to look for
4. **Keep It Simple** - Focused feature set, not an astronomy encyclopedia

---

## Phase 1: Foundation ✅ (Complete)

**Goal:** Basic sky tracking with core features

- [x] ISS pass predictions
- [x] Moon phases and rise/set times
- [x] Sun times (sunrise, sunset, twilight)
- [x] Aurora/space weather forecasts
- [x] Location management
- [x] Accessible UI with keyboard navigation
- [x] CI/CD pipeline

---

## Phase 2: Stargazing Companion (Current)

**Goal:** Help users plan stargazing sessions

- [x] Meteor shower calendar
- [x] Planet visibility
- [x] Eclipse calendar (2025-2030)
- [x] Dark sky times (astronomical twilight)
- [x] Viewing conditions score
- [ ] **Weather integration** - Cloud cover from Open-Meteo
- [ ] **Tonight's highlights** - Summary of what's visible tonight
- [ ] **Best viewing time** - Optimal window considering all factors

---

## Phase 3: Notifications & Alerts

**Goal:** Proactive alerts so users don't miss events

- [ ] ISS pass notifications (X minutes before visible pass)
- [ ] Meteor shower peak alerts
- [ ] Aurora activity alerts (Kp index threshold)
- [ ] Eclipse reminders
- [ ] "Clear skies tonight" alerts when conditions are good
- [ ] Customizable notification preferences

---

## Phase 4: Enhanced Data

**Goal:** Richer astronomical information

- [ ] Satellite passes beyond ISS (Starlink, Hubble, etc.)
- [ ] Constellation guide - What's overhead now
- [ ] Light pollution map/Bortle scale for location
- [ ] Comet tracking (when notable comets appear)
- [ ] Lunar eclipse visibility calculator
- [ ] Solar eclipse path maps

---

## Phase 5: Community & Sharing

**Goal:** Connect with other sky watchers

- [ ] Export/share viewing schedules
- [ ] Import location presets
- [ ] Observation logging
- [ ] Integration with astronomy communities (optional)

---

## Non-Goals (Out of Scope)

These are explicitly **not** planned to keep the app focused:

- ❌ Telescope control or astrophotography features
- ❌ Deep sky object catalogs (Messier, NGC)
- ❌ Star charts or planetarium view
- ❌ Professional astronomy calculations
- ❌ Paid API integrations
- ❌ Social features or accounts

---

## API Strategy

**Preferred (Free, No Key):**
- Open-Meteo - Weather, astronomy data
- Sunrise-Sunset.org - Sun times
- Open Notify - ISS position
- NOAA SWPC - Space weather

**Acceptable (Free Tier with Key):**
- N2YO - Satellite passes (if free tier sufficient)
- Visual Crossing - Weather backup

**Avoid:**
- Paid APIs
- APIs requiring registration/approval
- Unreliable or undocumented APIs

---

## Release Milestones

| Version | Phase | Target |
|---------|-------|--------|
| 0.1.0 | Phase 1 | ✅ Complete |
| 0.2.0 | Phase 2 | In Progress |
| 0.3.0 | Phase 3 | TBD |
| 1.0.0 | Phase 4 | TBD |

---

## Contributing

When adding features:
1. Check this roadmap first - is it in scope?
2. Prefer API calls over local calculations
3. All UI must have accessibility labels
4. Write tests before implementation (TDD)
5. Keep code simple - avoid over-engineering
