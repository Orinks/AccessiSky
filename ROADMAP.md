# AccessiSky Roadmap

A focused roadmap for AccessiSky - the accessible sky tracking companion to AccessiWeather.

## Vision

AccessiSky helps users stay connected to **what's happening above** — whether or not they can see it. Built primarily for blind and visually impaired users, but useful for everyone.

The app answers:
- "When is the ISS passing over?" (a shared experience, even without sight)
- "What phase is the moon in?" (affects tides, wildlife, cultural events)
- "When does it get dark tonight?" (practical daily planning)
- "Is there a meteor shower happening?" (events to know about and share)
- "Any space weather activity?" (aurora, solar storms)

## Core Principles

1. **Built for Screen Readers** - Every feature must be fully accessible
2. **Information, Not Just Visuals** - Focus on knowledge and awareness, not just "what to look at"
3. **API Over Calculation** - Use free APIs instead of local math where possible
4. **Practical & Social** - Help users plan their day and connect over shared celestial events
5. **Keep It Simple** - Focused feature set, not an astronomy encyclopedia

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

## Phase 2: Sky Awareness (Current)

**Goal:** Keep users informed about celestial events and conditions

- [x] Meteor shower calendar - Know when major showers are active
- [x] Planet positions - Which planets are in the sky
- [x] Eclipse calendar (2025-2030) - Upcoming eclipses worldwide
- [x] Dark sky times - When true night begins/ends
- [x] Conditions summary - Weather and moon factors
- [ ] **Weather integration** - Cloud cover and conditions from Open-Meteo
- [ ] **Tonight's summary** - Plain-language summary of sky events tonight
- [ ] **Daily briefing** - What's happening in the sky today

---

## Phase 3: Notifications & Alerts

**Goal:** Proactive alerts so users stay informed about events

- [ ] ISS pass notifications (X minutes before pass overhead)
- [ ] Meteor shower peak alerts (major showers like Perseids)
- [ ] Aurora activity alerts (high Kp index)
- [ ] Eclipse reminders (days before, then day-of)
- [ ] Space weather alerts (solar flares, geomagnetic storms)
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
