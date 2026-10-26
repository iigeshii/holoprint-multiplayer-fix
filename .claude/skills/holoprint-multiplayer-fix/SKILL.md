---
name: holoprint-multiplayer-fix
description: Patch HoloPrint Minecraft Bedrock .mcpack holograms in in/ so each player's hologram view is independent in multiplayer and the on-screen buttons / F10 keybind controls keep working with other players nearby; writes patched packs to out/. Use when the user adds HoloPrint packs to in/, asks to fix/patch a holoprint, or mentions holoprint controls breaking or desyncing with multiple players.
---

# HoloPrint multiplayer fix

Patches HoloPrint resource packs (no behavior pack needed) so each player's hologram view is independent and the controls keep working with others nearby:
- **Attachables are disabled on all players**, including you: the patch adds a copy of the vanilla `player.entity.json` (from the installed game) with `"enable_attachables": false`. Player armor and elytra aren't drawn on the patched screen, and shields/spears/spyglass/mace in hand show as plain items; gameplay is unaffected. Confirmed in game: the F10/button controls die while a nearby friend wears armor (a netherite chestplate is a reliable trigger) and work the moment it's removed; holding armor is fine. Status: **v1.3.10 confirmed working** on a Realm — F10 controls work with an armored player nearby; no armor is visible on any player.
- Only the **local player** drives player controls (swinging control items) and hologram backups. Unpatched, every player model on screen overwrites the shared action temp variables, so nearby players swallow your inputs and their swings change your hologram.
- Armor stand pose / held item / punching stay **shared** on purpose: they're server-synced.
- Pack name becomes `<file name minus .holoprint.mcpack> (MP fix <version>)` — HoloPrint names packs after the structure, so different files can share a name, and Minecraft's pack list doesn't show versions. `PATCH_REVISION` is added to the version (same UUID, so it imports as an upgrade).

## Run it

From the project root:

```
python -I .claude/skills/holoprint-multiplayer-fix/patch_holoprint.py
```

This patches every `in/*.mcpack` into `out/<name>.mpfix.mcpack`, overwriting earlier outputs. A single file also works: `patch_holoprint.py <input.mcpack> [output.mcpack]`. Unpacked folders in `in/` are ignored.

The player entity is copied from the **installed Minecraft** (`C:/XboxGames/Minecraft for Windows/Content/data/resource_packs`, newest `vanilla_*` definition; override with the `MC_RESOURCE_PACKS` env var). Entity files don't merge, so a stale copy shadows Minecraft's own player changes: **after every Minecraft update, re-run and re-import**. It can also conflict with other packs that override the player entity (custom player models); the higher pack wins.

Report each pack's result to the user (OK/FAIL, output path, pack name and version). If `in/` is empty, tell the user to drop HoloPrint `.mcpack` files there. Remind them: import the patched pack and activate it (world resource packs, or Settings → Global Resources per player). Each player who wants working controls needs the patched pack; it only changes what that player's own screen shows. The game is on a Realm; that doesn't matter, everything here is client-side.

## When the patch itself changes

Increase `PATCH_REVISION` in the script. Minecraft silently ignores an import whose version isn't higher than the installed one, so without a bump users keep running the old patch. Old versions pile up in the user's `resource_packs` folder (`TownHall_2`, `TownHall_2(1)`, ...); `global_resource_packs.json` shows which version is active.

## If a pack fails

- `already patched` — the input is already a patched pack; nothing to do.
- `not a HoloPrint pack?` — missing `manifest.json` or the player render controller file.
- `no vanilla entity found` — Minecraft isn't at the default path; find its `data/resource_packs` folder and set `MC_RESOURCE_PACKS`.
- `HoloPrint version not supported` — a newer HoloPrint changed the code the patch anchors on. Adapt the script (below), then re-run on all of `in/`.

### Adapting to a new HoloPrint version

Extract the failing pack into a fresh folder in the scratchpad (not the project) and inspect:

- `render_controllers/player.render_controllers.json` — the `textures[0]` Molang expression of `controller.render.player.first_person` and `.third_person`. HoloPrint hides control logic there: it detects swings with control items, sets `t.player_action` / `t.player_action_counter`, and syncs `t.hologram_backup_*`. The patch adds `&&q.is_local_player` to the opening guard condition (`!q.is_in_ui...?{`). Update `GUARDS` to the new opening text.
- `subpacks/*/entity/armor_stand.entity.json` — `pre_animation` reads `t.ui_action` / `t.ui_action_counter` (written by the invisible UI armor stands in `ui/holoprint_common.json`, rendered by the HUD buttons/keybinds) and `t.player_action*`.

Vanilla files live in `.brarchive` files under each `vanilla_*/__brarchive/` (header: 8-byte magic, u32 count, u32 version; then 256-byte entries: u8 name length, name, u32 offset and u32 length at byte 248; data follows the entry table). `read_brarchive` in the script parses them.

Background: HoloPrint is resource-pack only. All hologram state is client-side Molang `v.` variables, and controls reach the armor stand through `t.` temp variables leaking between entities in the same frame. That's why views are per-player, and why anything drawn in between that resets temp variables (attachables) breaks controls. A shared view would need a behavior pack with entity properties and server-side UI (`@minecraft/server-ui`); HUD buttons can never reach the server.

### Tested and ruled out

- Re-publishing the button action from the local player's render controller every frame: controls still died with armored players nearby (first-person player draws after the world).
- (v1.3.5–1.3.8) Overriding vanilla **attachable** files by identifier (`attachables/...` with changed `item` maps, gated scripts/render controllers, or script-free copies): Minecraft ignored them all — armor still showed on everyone, including the user's own in F5. Attachables can't be overridden from a resource pack this way; render controllers and entities can (by identifier). Earlier "armor invisible" reports were mistaken (helmet hidden by blond hair), so no attachable-level hypothesis was actually tested.

- (v1.3.9) Overriding the vanilla render controller `controller.render.armor.player` (shared by all `*.player` armor and the elytra) with `part_visibility` `query.is_local_player`: worked as drawn — other players' armor invisible, own armor visible — but controls still died. The attachable's existence (its scripts / render-controller evaluation), not drawing it, is the trigger. Since attachable files can't be overridden and `enable_attachables` is per entity type, the only remaining switch disables attachables on all players.

Possible follow-up to show armor again: draw it from the player entity's own render controllers (entity render controllers don't wipe temp variables — HoloPrint's own player render controller runs every frame). Add one render controller per armor slot to the overridden player entity, choosing geometry/texture with `q.is_item_name_any('slot.armor.*', ...)`; loses enchant glint, trims and leather dye color.

Not covered: armored **mobs** or armor stands wearing armor near the hologram may still interrupt controls (they keep their attachables).
