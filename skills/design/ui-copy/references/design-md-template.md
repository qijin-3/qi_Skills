# design.md output template

Downstream agents consume this file as the single source of truth for visual implementation. Prefer precise, semantic English: descriptive names + exact values + functional roles. Do not write marketing copy.

Fill every section from the reference images. If a section cannot be observed, write `Not observable in references — [brief guess or omit]` rather than inventing a full system.

---

```markdown
# Design System: [Project or Source Title]

**Source:** [file names / URLs of references]
**Extracted:** [ISO date]
**Fidelity:** Faithful extraction from provided references (provider taste trusted)
**Skill:** UI Copy

---

## Configuration — Observed Style Dials

Score 1–10 from what the references actually show (not aspirational taste).

| Dial | Level | Evidence |
|------|-------|----------|
| **Creativity** | `N` | [what in the images supports this] |
| **Density** | `N` | whitespace vs information packing |
| **Variance** | `N` | symmetry vs asymmetry across sections |
| **Motion Intent** | `N` | static cues only unless motion is visible / described |

---

## 1. Visual Theme & Atmosphere

[2–4 sentences. Mood, material feel, light/dark, density, how expensive/utilitarian/playful it feels. Ground claims in visible traits.]

## 2. Color Palette & Roles

List every recurring color. Format: **Descriptive Name** (`#HEX` or `rgba(...)`) — role.

- **[Name]** (#XXXXXX) — [background / text / accent / border / shadow / …]
- …

### Accent usage
[How many accents? Where do they appear? Gradients? Glass?]

### Surfaces & elevation
[Background layers, card fills, blur/glass, border treatment, shadow recipe if visible]

### Inferred / approximate note
[Call out any hex values that are approximate samples from pixels]

## 3. Typography Rules

- **Display / Headlines:** [family if identifiable, else describe: geometric sans / humanist / serif / mono], weight, tracking, leading, size feel (`clamp` or rem if inferable)
- **Body:** […]
- **Mono / Meta:** […] if present
- **Scale hierarchy:** [H1 / H2 / body / caption relationships]
- **Case & decoration:** [ALL CAPS labels, underline links, etc.]

If the font cannot be identified, name closest public alternatives and mark them `inferred`.

## 4. Component Stylings

For each visible component type, describe shape, fill, border, radius, shadow, and interaction cues if shown:

* **Buttons:** primary / secondary / ghost / destructive
* **Cards / containers:**
* **Inputs / forms:**
* **Navigation:**
* **Chips / badges / tags:**
* **Tables / lists:**
* **Modals / sheets:**
* **Loaders / empty / error:** (only if present)

Omit types that never appear in the references.

## 5. Layout Principles

- **Structure:** [grid, bento, split, single column, sidebar, …]
- **Hero / first viewport:** [composition rules as shown]
- **Spacing rhythm:** [tight / medium / airy; recurring gap sizes if readable]
- **Alignment & asymmetry:**
- **Max width / containment:** [if inferable]
- **Imagery treatment:** [full-bleed, inset, rounded media, collage, …]

## 6. Responsive Hints

Only what the references support (multiple breakpoints, mobile frames, etc.). If only desktop is provided, say so and list safe collapse assumptions without inventing a second visual language.

## 7. Motion & Interaction (if evidenced)

Document only motion that is visible, implied by UI chrome, or explicitly described by the user. Otherwise: `No motion evidenced — keep static unless product later specifies.`

## 8. Do-Not-Diverge (Fidelity Guards)

List patterns that would **break** fidelity to these references — derived from the images, not from external taste bans.

Examples of form (rewrite to match the actual references):
- Do not replace the observed accent `[color]` with a different brand accent
- Do not switch the observed radius language (`Npx` / pill / sharp) to another system
- Do not introduce layout patterns absent from references (e.g. equal 3-card rows) unless required by new content
- …

## 9. Open Questions

Bullet anything ambiguous (exact font file, dark-mode twin, token names, icon set). Ask the human only if blocking.
```
