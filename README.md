# HoloPrint multiplayer fix

A patcher for [HoloPrint](https://github.com/SuperLlama88888/holoprint) hologram packs (Minecraft: Bedrock Edition). It fixes two problems that show up when more than one player is near a hologram:

1. **The on-screen buttons and F10 keyboard controls stop working** as soon as another player wearing armor comes near.
2. **Players' views interfere with each other**: another player's swing with a control item could change your layer, and their game could swallow your inputs.

After patching, every player has their own independent hologram view and the controls keep working.

> **Credit:** HoloPrint is made by [SuperLlama88888](https://github.com/SuperLlama88888) and contributors. All the hologram magic is theirs. This project only adjusts the packs HoloPrint creates. It is **unofficial** and **not affiliated with or endorsed by HoloPrint**. Please report problems with patched packs here, not to HoloPrint.

## What it changes

HoloPrint packs are resource packs only. The hologram's state lives on each player's own device. The controls reach the hologram through Molang temporary variables that the game passes between entities as it draws each frame. Two things break that in multiplayer:

- **Every player model on screen overwrote the control signal**, so nearby players' stale values swallowed yours. The patch makes only *your own* player send control actions.
- **Attachables wipe the signal.** In current Minecraft, worn armor (plus elytra, shields, spears, the spyglass and the mace) uses "attachable" models. Just having one on a nearby player clears the variables the controls depend on, even if it isn't drawn. A resource pack can't disable attachables per player, so the patch turns them off for all players. It then **redraws armor directly on the player model**, which doesn't break the controls.

### Trade-offs on the patched screen

These are visual only. Gameplay and armor protection are unaffected.

- Armor shows its basic look but **no enchantment glint, no trims, and leather appears undyed**.
- **Elytra aren't drawn**, and **shields, spears, the spyglass and the mace show as flat item icons** in hand.
- You don't see your own armor sleeves in first person.
- Armored mobs or armor stands right next to the hologram may still interrupt the controls.
- The patched pack includes a copy of Minecraft's player definition, which **must be refreshed after every Minecraft update**: re-run the patcher and re-import.

The armor stand controls (giving it an item and punching it, changing its pose) still affect everyone's view. That's by design: the server shares those with all players.

## Usage

Requirements: Python 3.9+ and Minecraft Bedrock installed on the same Windows PC. The patcher reads a few game files from your install, so no Minecraft files are included in this repository.

1. Put HoloPrint `.mcpack` files in `in/`.
2. Run:
   ```
   python .claude/skills/holoprint-multiplayer-fix/patch_holoprint.py
   ```
   Patched packs appear in `out/` as `<name>.mpfix.mcpack`. In Minecraft they're named `<name> (MP fix <version>)`.
3. Import the patched pack and activate it: in the world's resource packs, or per player under **Settings → Global Resources**. Each player who wants working controls needs the patched pack; it only changes what that player's own screen shows.

If Minecraft isn't installed at `C:\XboxGames\Minecraft for Windows`, set `MC_RESOURCE_PACKS` to the game's `Content\data\resource_packs` folder.

To patch a single file instead of everything in `in/`, pass it as an argument: `patch_holoprint.py <input.mcpack> [output.mcpack]`.

### With Claude Code

The patcher is packaged as a [Claude Code](https://claude.com/claude-code) skill. Open this folder in Claude Code and run `/holoprint-multiplayer-fix`, or just ask it to patch your holograms. The skill's [SKILL.md](.claude/skills/holoprint-multiplayer-fix/SKILL.md) also documents how the fix works, what was tried and ruled out, and how to adapt it if a new HoloPrint or Minecraft version changes things.

## Compatibility

Developed and tested with packs from HoloPrint 1.3.3 on Minecraft Bedrock 1.26.x for Windows, on a Realm. If a future HoloPrint changes the code the patch relies on, the patcher stops with "HoloPrint version not supported" rather than producing a broken pack.

## License

- **This project's code and docs** are under the [MIT License](LICENSE).
- **Patched packs remain HoloPrint's work under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)**, per [HoloPrint's Terms of Use](https://github.com/SuperLlama88888/holoprint/blob/main/TERMS_OF_USE.md). You may share them for free with credit, but you may not sell them or put them behind ads or paid downloads. The patcher keeps HoloPrint's authors, license and links in every pack and marks the pack as modified with a link back here.
- No HoloPrint packs or Minecraft files are included in this repository.

Minecraft is a trademark of Mojang Synergies AB. This project is not affiliated with Mojang or Microsoft.
