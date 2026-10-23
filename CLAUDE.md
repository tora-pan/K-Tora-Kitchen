## Unity Development Best Practices

### Architecture
- Follow Unity conventions and use the Unity APIs appropriate for the installed editor version.
- Prefer simple, modular, composition-based designs over deep inheritance hierarchies.
- Use MonoBehaviours for scene behavior and ScriptableObjects for reusable game configuration and data.
- Separate game logic from UI, input, and presentation where practical.
- Avoid introducing design patterns, abstractions, managers, interfaces, or frameworks unless they solve a real current problem.
- Avoid global singletons and static mutable state unless clearly justified.
- Keep the project suitable for a solo developer to understand and maintain.

### C# Standards
- Use clear, descriptive names and consistent C# formatting.
- Follow standard C# naming conventions: PascalCase for types and public members, camelCase for local variables and private fields.
- Serialize private Inspector fields with `[SerializeField]` when needed rather than making fields public unnecessarily.
- Prefer `[RequireComponent]` where a component dependency is mandatory.
- Use explicit types when they improve readability; use `var` when the type is obvious.
- Avoid unnecessary LINQ, allocations, reflection, and per-frame work in `Update()`.
- Cache component references when appropriate.
- Use events or direct references for communication when they keep dependencies simple.
- Handle missing references and invalid state deliberately; do not silently swallow exceptions.
- Do not add comments that merely restate the code.

### Unity Scene and Asset Practices
- Preserve Unity `.meta` files and existing asset GUIDs. Never delete or regenerate them unnecessarily.
- Do not manually edit Unity scene, prefab, or project configuration files when the Unity Editor or a supported Unity API is the safer option.
- Do not assume scene objects, components, tags, layers, or Inspector references exist. Inspect the project first.
- Keep scene setup and required Inspector assignments documented.
- Prefer reusable prefabs for repeated entities such as customers, trucks, and furniture.
- Use ScriptableObjects for data-driven content such as recipes, upgrades, trucks, locations, and employees.
- Keep gameplay assets organized in the existing folder structure.
- Avoid adding packages or plugins unless necessary and approved.

### Performance
- Target stable performance on typical PC gaming hardware.
- Avoid expensive work in `Update()` when it can be event-driven or performed less frequently.
- Avoid repeated `FindObjectOfType`, `GameObject.Find`, scene searches, and component lookups during gameplay loops.
- Use object pooling only when profiling or repeated spawning makes it worthwhile.
- Avoid premature optimization; prioritize simple, correct implementations and profile actual bottlenecks.
- Keep customer counts, AI behavior, and simulation complexity appropriate for the current prototype.

### Game Design
- Prioritize a playable core loop over content volume and polish.
- Build features in small increments that can be tested independently.
- Use placeholder shapes, materials, and UI until the gameplay is proven.
- Keep game rules, economy values, and progression configurable rather than scattering magic numbers throughout scripts.
- Make customer behavior and food preparation predictable enough to debug.
- Do not implement future features unless explicitly requested.

## AI-Assisted Development and Token Efficiency

### Before Making Changes
- Read this file and inspect only the project files relevant to the current task.
- Check the Unity version, installed packages, existing architecture, and current scene setup when relevant.
- Summarize the proposed implementation briefly before making substantial changes.
- Do not repeatedly re-read files that have not changed or summarize the entire repository unnecessarily.
- Ask a concise clarification only when a missing decision materially affects the implementation.

### Implementation Rules
- Solve the immediate task with the smallest maintainable change.
- Reuse existing scripts, components, prefabs, and conventions before creating new ones.
- Do not rewrite working systems to match personal preferences.
- Do not create extra documentation, test frameworks, helper classes, or configuration files unless they provide concrete value for the current task.
- Avoid speculative features, excessive defensive code, and unnecessary dependencies.
- Do not change unrelated files or reformat entire files without a reason.
- Do not duplicate code or create multiple competing implementations of the same system.
- If a task is large, split it into small, independently testable steps.

### Output Efficiency
- Keep explanations concise and focused on decisions, changed files, setup steps, and test results.
- Do not print entire source files when a brief summary or diff is sufficient.
- Report only relevant warnings, errors, and unresolved issues.
- Do not claim code compiles or gameplay works unless it has actually been verified.
- If Unity Editor interaction or manual Inspector setup is required, provide exact, minimal steps.
- Avoid lengthy plans for small tasks and lengthy summaries after simple changes.

## Testing and Verification

- Validate changes with the available tools before claiming success.
- Check for compile errors and obvious runtime issues.
- Do not assume Unity can be controlled or tested directly from the terminal.
- When Editor testing is unavailable, clearly state what remains unverified.
- Provide a short Play Mode test checklist for each gameplay feature.
- Prefer targeted tests for critical game logic when practical, without introducing a testing framework prematurely.

## Change Safety

- Never delete assets, scenes, prefabs, packages, or project settings without explicit approval.
- Never overwrite substantial existing work without explaining the impact first.
- Do not run destructive shell commands or discard user changes.
- Inspect Git status before significant changes and preserve unrelated uncommitted work.
- Do not commit changes unless explicitly asked.
- If a requested change requires modifying project settings or installing dependencies, explain why before proceeding.

## Current Development Priorities

1. Get a complete customer order loop working.
2. Add soba preparation and serving.
3. Add payments and a basic cash economy.
4. Add a small number of visible, functional upgrades.
5. Add save/load.
6. Polish visuals only after the loop is fun and reliable.

The current prototype is the priority. Do not build a full production architecture before the prototype proves itself.