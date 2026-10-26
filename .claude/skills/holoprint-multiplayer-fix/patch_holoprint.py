"""Patch HoloPrint .mcpack files so each player's hologram view is independent in multiplayer
and the on-screen buttons / F10 keybind controls keep working with other players nearby.

Usage:
  python patch_holoprint.py                      # every in/*.mcpack -> out/<name>.mpfix.mcpack
  python patch_holoprint.py <input.mcpack> [output.mcpack]

in/ and out/ are relative to the project root (three levels above this skill folder).
The vanilla player entity is read from the installed Minecraft; override the location with the
MC_RESOURCE_PACKS environment variable (the folder holding vanilla_* packs).

Changes:
  1. render_controllers/player.render_controllers.json: only the local player publishes
     player-control actions (t.player_action*) and hologram backups. Previously every player
     model on screen overwrote these each frame, so other players' stale counters swallowed
     your inputs and their swings changed your hologram.
  2. entity/holoprint_mpfix.player.entity.json: copy of the vanilla player client entity with
     enable_attachables off, for every player including you. Having an attachable (worn armor,
     elytra, shield...) wipes Molang temp variables even when it isn't drawn, and that is how
     HoloPrint's controls reach the armor stand - so a nearby player wearing armor broke them.
  3. manifest.json: PATCH_REVISION is added to the patch version, so it imports as an upgrade,
     and the pack name becomes "<file name minus .holoprint.mcpack> (MP fix <version>)".

Armor stand pose / held item / punching are server-synced and intentionally left shared.
"""
import json
import os
import re
import struct
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
IN_DIR = PROJECT_ROOT / "in"
OUT_DIR = PROJECT_ROOT / "out"
OUT_SUFFIX = ".mpfix.mcpack"
MC_RESOURCE_PACKS = Path(os.environ.get("MC_RESOURCE_PACKS", "C:/XboxGames/Minecraft for Windows/Content/data/resource_packs"))

RC_PATH = "render_controllers/player.render_controllers.json"
PLAYER_ENTITY_PATH = "entity/holoprint_mpfix.player.entity.json"
MANIFEST_PATH = "manifest.json"
NAME_SUFFIX = "MP fix"
# Added to the pack's patch version. Increase whenever the patch changes: Minecraft ignores an
# import whose version isn't higher than the one already installed.
PATCH_REVISION = 7

GUARDS = {
	"controller.render.player.first_person": "!q.is_in_ui&&!v.map_face_icon?{",
	"controller.render.player.third_person": "!q.is_in_ui?{",
}

class PatchError(Exception):
	pass

def read_brarchive(path):
	"""Yield (name, bytes) from a Mojang .brarchive file."""
	data = path.read_bytes()
	count, _version = struct.unpack_from("<II", data, 8)
	base = 16 + count * 256
	for i in range(count):
		entry = 16 + i * 256
		name = data[entry + 1:entry + 1 + data[entry]].decode()
		offset, length = struct.unpack_from("<II", data, entry + 248)
		yield name, data[base + offset:base + offset + length]

def load_vanilla_file(archive_name, file_name):
	"""Latest version of a vanilla file, from the installed game's vanilla_* packs. Returns (json, pack name)."""
	archives = list(MC_RESOURCE_PACKS.glob(f"vanilla*/__brarchive/{archive_name}.brarchive"))
	if not archives:
		raise PatchError(f"no vanilla {archive_name} found under {MC_RESOURCE_PACKS} - set MC_RESOURCE_PACKS to the game's data/resource_packs folder")
	version_of = lambda archive: [int(x) for x in re.findall(r"\d+", archive.parts[-3])]
	found = None
	for archive in sorted(archives, key=version_of):
		for name, content in read_brarchive(archive):
			if name == file_name:
				found = (json.loads(content), archive.parts[-3])
	if not found:
		raise PatchError(f"{file_name} not found in the installed game")
	return found

def build_player_entity(player_entity):
	"""Vanilla player client entity with attachables disabled, for every player including you.
	Merely having an attachable (worn armor, elytra, shield...) wipes the temp variables, even when
	it isn't drawn; enable_attachables is the only per-entity-type switch a resource pack has."""
	player_entity["minecraft:client_entity"]["description"]["enable_attachables"] = False
	return player_entity

def patch_render_controllers(data):
	rcs = data["render_controllers"]
	for name, guard in GUARDS.items():
		if name not in rcs:
			raise PatchError(f"{name} missing - HoloPrint version not supported")
		textures = rcs[name]["textures"]
		expr = textures[0]
		if "q.is_local_player" in expr:
			raise PatchError("already patched")
		if not expr.startswith(guard):
			raise PatchError(f"{name}: unexpected expression start - HoloPrint version not supported")
		textures[0] = guard[:-2] + "&&q.is_local_player?{" + expr[len(guard):]

def patch_manifest(manifest, pack_name):
	for section in [manifest["header"], *manifest["modules"]]:
		section["version"][2] += PATCH_REVISION
	# Minecraft's pack list doesn't show versions, so put it in the name
	version = ".".join(map(str, manifest["header"]["version"]))
	manifest["header"]["name"] = f"{pack_name} ({NAME_SUFFIX} {version})"
	return manifest["header"]

def dump(data):
	return json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def patch_pack(src, dst, player_entity):
	"""Patch src into dst. Returns the new manifest header. Raises PatchError on failure."""
	with zipfile.ZipFile(src) as zin:
		names = set(zin.namelist())
		for required in (RC_PATH, MANIFEST_PATH):
			if required not in names:
				raise PatchError(f"{required} not found - not a HoloPrint pack?")
		if PLAYER_ENTITY_PATH in names:
			raise PatchError("already patched")
		entries = []
		for info in zin.infolist():
			content = zin.read(info)
			if info.filename == RC_PATH:
				rc = json.loads(content)
				patch_render_controllers(rc)
				content = dump(rc)
			elif info.filename == MANIFEST_PATH:
				manifest = json.loads(content)
				# HoloPrint names packs after the structure, which can repeat across files; use the file name instead
				header = patch_manifest(manifest, src.name.removesuffix(".mcpack").removesuffix(".holoprint"))
				content = dump(manifest)
			entries.append((info.filename, content))
	entries.append((PLAYER_ENTITY_PATH, dump(player_entity)))
	# Only write once everything patched cleanly, so failures never leave a half-written pack.
	dst.parent.mkdir(parents=True, exist_ok=True)
	with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
		for path, content in entries:
			zout.writestr(path, content)
	return header

def report(src, dst, header):
	version = ".".join(map(str, header["version"]))
	shown = dst.relative_to(PROJECT_ROOT) if dst.is_relative_to(PROJECT_ROOT) else dst
	print(f"OK    {src.name} -> {shown}  ('{header['name']}' v{version})")

def main():
	try:
		player_entity, source = load_vanilla_file("entity", "player.entity.json")
	except PatchError as e:
		raise SystemExit(f"FAIL  {e}")
	player_entity = build_player_entity(player_entity)
	print(f"Using player.entity.json from Minecraft's {source} files\n")

	if len(sys.argv) > 1:
		src = Path(sys.argv[1])
		dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name(src.name.removesuffix(".mcpack") + OUT_SUFFIX)
		try:
			report(src, dst, patch_pack(src, dst, player_entity))
		except PatchError as e:
			raise SystemExit(f"FAIL  {src.name}: {e}")
		return
	IN_DIR.mkdir(exist_ok=True)
	OUT_DIR.mkdir(exist_ok=True)
	packs = sorted(IN_DIR.glob("*.mcpack"))
	if not packs:
		print(f"No .mcpack files in {IN_DIR}")
		return
	failures = 0
	for src in packs:
		dst = OUT_DIR / (src.name.removesuffix(".mcpack") + OUT_SUFFIX)
		try:
			report(src, dst, patch_pack(src, dst, player_entity))
		except PatchError as e:
			print(f"FAIL  {src.name}: {e}")
			failures += 1
	print(f"\n{len(packs) - failures} patched, {failures} failed")
	sys.exit(1 if failures else 0)

if __name__ == "__main__":
	main()
