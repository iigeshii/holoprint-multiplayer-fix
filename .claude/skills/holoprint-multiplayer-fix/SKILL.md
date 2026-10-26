---
name: holoprint-multiplayer-fix
description: Patch HoloPrint Minecraft Bedrock .mcpack holograms in in/ so each player's hologram view is independent in multiplayer and the on-screen buttons / F10 keybind controls keep working with other players nearby; writes patched packs to out/. Use when the user adds HoloPrint packs to in/, asks to fix/patch a holoprint, or mentions holoprint controls breaking or desyncing with multiple players.
---

# HoloPrint multiplayer fix

Patches packs made by [HoloPrint](https://github.com/SuperLlama88888/holoprint) (by SuperLlama88888, CC BY-NC-SA 4.0). This project is unofficial and not affiliated with HoloPrint. Patched packs keep HoloPrint's authors, license and links, and are marked as modified.

The patch is resource-pack only (no behavior pack needed). Each player's hologram view is independent, and the controls keep working with others nearby:
- **Attachables are disabled on all players**, including the local one: the patch adds a copy of the vanilla `player.entity.json` (from the installed game) with `"enable_attachables": false`. Merely having an attachable (worn armor especially) wipes the temp variables HoloPrint's controls depend on, even when it isn't drawn. Shields, spears, the spyglass and the mace in hand show as plain items, and elytra aren't drawn. Gameplay is unaffected.
- **Armor is redrawn** by four extra player render controllers (`controller.render.holoprint_mpfix.armor.<slot>`, in `render_controllers/holoprint_mpfix.armor.render_controllers.json`). They use the geometry and textures of the vanilla `*.player` armor attachables, picked with `q.is_item_name_any('slot.armor.*', ...)`. Third person only, with no enchant glint, trims or leather dye. The skin's outer layers are hidden under worn armor via `v.chest/leg/boot_layer_visible` in `pre_animation`.
- Only the **local player** drives player controls (swinging control items) and hologram backups. Unpatched, every player model on screen overwrites the shared action temp variables, so nearby players swallow your inputs and their swings change your hologram.
- Armor stand pose / held item / punching stay **shared** on purpose: they're server-synced.
- **Manifest:**
  - The pack name becomes `<file name minus .holoprint.mcpack> (MP fix <version>)`. HoloPrint names packs after the structure, so different files can share a name, and Minecraft's pack list doesn't show versions.
  - `PATCH_REVISION` is added to the version (same UUID, so it imports as an upgrade).
  - `metadata.generated_with` gains `holoprint_multiplayer_fix`, and the pack settings get a "Modified by" entry linking to `PROJECT_URL`.

Confirmed in game (Bedrock 1.26.x, on a Realm with two players): controls die while a nearby player wears armor and work the moment it's removed. Holding armor is fine. With the patch, controls work with an armored player nearby and armor is visible.

## Run it

From the project root:

```
python -I .claude/skills/holoprint-multiplayer-fix/patch_holoprint.py
```

This patches every `in/*.mcpack` into `out/<name>.mpfix.mcpack`, overwriting earlier outputs. A single file also works: `patch_holoprint.py <input.mcpack> [output.mcpack]`. Unpacked folders in `in/` are ignored.

The player entity and armor attachables are read from the **installed Minecraft**: `C:/XboxGames/Minecraft for Windows/Content/data/resource_packs`, newest `vanilla_*` definition. Override with the `MC_RESOURCE_PACKS` env var. Entity files don't merge, so a stale copy shadows Minecraft's own player changes: **after every Minecraft update, re-run and re-import**. It can also conflict with other packs that override the player entity (custom player models); the higher pack wins.

Report each pack's result to the user: OK/FAIL, output path, pack name and version. If `in/` is empty, tell the user to drop HoloPrint `.mcpack` files there. Remind them:
- Import the patched pack and activate it (world resource packs, or Settings → Global Resources per player).
- Each player who wants working controls needs the patched pack. It only changes what that player's own screen shows, so Realms and servers work the same as local worlds.
- Patched packs stay under HoloPrint's CC BY-NC-SA 4.0: free to share, not to sell or put behind ads.

## When the patch itself changes

Increase `PATCH_REVISION` in the script. Minecraft silently ignores an import whose version isn't higher than the installed one, so without a bump users keep running the old patch. Old versions pile up in the user's `resource_packs` folder (`<name>`, `<name>(1)`, ...). `global_resource_packs.json` shows which version is active.

## If a pack fails

- `already patched`: the input is already a patched pack; nothing to do.
- `not a HoloPrint pack?`: `manifest.json` or the player render controller file is missing.
- `no vanilla entity found`: Minecraft isn't at the default path. Find its `data/resource_packs` folder and set `MC_RESOURCE_PACKS`.
- `player armor attachables not found`: Minecraft changed how player armor is drawn. Inspect the attachables archive (below) and adapt `player_armor_pieces`.
- `HoloPrint version not supported`: a newer HoloPrint changed the code the patch anchors on. Adapt the script (below), then re-run on all of `in/`.

### Adapting to a new HoloPrint version

Extract the failing pack into a fresh folder in the scratchpad (not the project) and inspect:

- `render_controllers/player.render_controllers.json`: the `textures[0]` Molang expression of `controller.render.player.first_person` and `.third_person`. HoloPrint hides control logic there. It detects swings with control items, sets `t.player_action` / `t.player_action_counter`, and syncs `t.hologram_backup_*`. The patch adds `&&q.is_local_player` to the opening guard condition (`!q.is_in_ui...?{`). Update `GUARDS` to the new opening text.
- `subpacks/*/entity/armor_stand.entity.json`: `pre_animation` reads `t.ui_action` / `t.ui_action_counter` and `t.player_action*`. The `t.ui_action*` values are written by the invisible UI armor stands in `ui/holoprint_common.json`, which the HUD buttons/keybinds render.

Vanilla files live in `.brarchive` files under each `vanilla_*/__brarchive/`. `read_brarchive` in the script parses them. Format:
- Header: 8-byte magic, u32 count, u32 version.
- Then one 256-byte entry per file: u8 name length, the name, and at byte 248 a u32 offset and u32 length.
- The data follows the entry table.

Background: HoloPrint is resource-pack only. All hologram state is client-side Molang `v.` variables, and controls reach the armor stand through `t.` temp variables leaking between entities in the same frame. That's why views are per-player, and why attachables, which reset temp variables, break the controls. A shared view would need a behavior pack with entity properties and server-side UI (`@minecraft/server-ui`); HUD buttons can never reach the server.

### Tested and ruled out

- **Re-publishing the button action** from the local player's render controller every frame: controls still died with armored players nearby. The first-person player draws after the world.
- **(v1.3.5–1.3.8) Overriding vanilla attachable files by identifier** (`attachables/...` with changed `item` maps, gated scripts/render controllers, or script-free copies): Minecraft ignored them all, and armor still showed on everyone. Attachables can't be overridden from a resource pack this way; render controllers and entities can (by identifier).
- **(v1.3.9) Hiding armor on other players** by overriding the vanilla render controller `controller.render.armor.player` with `part_visibility` `query.is_local_player`: other players' armor became invisible, but controls still died. The attachable's existence, not drawing it, is the trigger. `enable_attachables` is per entity type, hence disabling attachables on all players and redrawing armor from the player entity.

Not covered: armored **mobs** or armor stands wearing armor near the hologram may still interrupt controls (they keep their attachables).
