# Rotom v0.4

Rotom is a Pokémon GO + Wayfarer Discord assistant.

## Added in v0.4

### Deterministic PvP IV engine

- Loads Pokémon base stats from PvPoke's Game Master JSON.
- Calculates CP using the Pokémon GO CPM table.
- Tests all 4,096 IV combinations for each league.
- Finds the highest legal half-level under the CP cap.
- Calculates stat product and ranks the requested IV spread.
- Calculates best stat-product IV spread for Great, Ultra and Master.
- Keeps deterministic math separate from the AI so Rotom does not hallucinate IV ranks.

### Shadow / Purified / Best Buddy / Form support

- Form-aware Game Master resolution (Alolan, Galarian, Hisuian, Origin, etc.).
- Shadow Pokémon use the 1.2× Attack / 0.83333331× Defense battle modifiers while keeping normal CP calculation.
- Purified is treated as a state label because the screenshot IVs already represent the current post-purification IVs.
- Best Buddy enables the level 51 PvP cap.
- `/rankcheck` exposes form, shadow, purified and best-buddy options.
- Prefix commands accept `shadow`, `purified` and `bestbuddy` flags.

### Screenshot rankcheck

`/rankcheck <screenshot>` and `!rankcheck` + image now send the screenshot to the configured OpenAI vision model for structured extraction of:

- Pokémon
- form
- CP
- Attack IV
- Defense IV
- Stamina IV
- weather boost
- shadow/purified status

The extracted IVs are then passed to the deterministic IV engine. If the vision model cannot confidently read the bars, Rotom refuses to guess.

## Commands

- `@Rotom <question>`
- `/rules`
- `/sync`
- `/rankcheck <screenshot>`
- `!rankcheck` + screenshot
- `!rank <pokemon>`
- `!pvpiv <pokemon>`
- `!pvpiv <pokemon> <attack> <defense> <stamina>`
- `!haversine <lat1> <lon1> <lat2> <lon2>`
- `!help_rotom`

## Data source

PvPoke publishes its Game Master data and generated PvP ranking data in its open-source repository. The bot caches the Game Master locally after the first successful download. PvPoke's rankings and simulation methodology can change over time.

## Important scope note

This v0.4 IV rank is **stat-product ranking**, not a battle-simulation ranking. It is intended to reproduce the standard PvP IV-rank concept used by IV calculators. Shadow battle modifiers, Best Buddy level 51, and form-aware stat resolution are now included in the deterministic IV engine. Purified is a metadata state because the supplied IVs are assumed to be the current appraisal IVs.
