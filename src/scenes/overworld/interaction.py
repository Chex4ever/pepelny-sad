"""World tile interactions and battles."""
from __future__ import annotations

from src.story.dialogues import get_dialogue, get_dialogue_speaker
from src.story.voices import voice_for_dialogue
from src.world.companions import companion_pos_for_player, has_service


class OverworldInteraction:
    def __init__(self, scene):
        self.scene = scene

    def battle_for_tile(self, ch: str, wx: int, wy: int) -> str | None:
        if ch != "!":
            return None
        key = (wx, wy, self.scene.game.world_state.layer)
        if key in self.scene.game.world_state.defeated_battles:
            return None
        if self.scene.game.world_state.layer == "dungeon":
            return "warden" if self.scene.game.world_state.dungeon_entered else "sorrow"
        if wy > 30:
            return "sorrow"
        if abs(wx) > 40:
            return "whisper"
        return "whisper"

    def interact(self) -> None:
        ow = self.scene
        layer = ow.game.world_state.layer
        px, py = ow.player.tile_pos()
        for dx, dy in [(0, 0), ow.player.facing, (1, 0), (-1, 0), (0, 1), (0, -1)]:
            tx, ty = px + dx, py + dy
            ch, _, _ = ow.game.world_map.get_tile(tx, ty, layer)
            if ch == "o":
                active, _ = ow.weather.on_turn(ow.fov.in_shelter())
                if active and layer == "surface" and not ow.fov.in_shelter():
                    ow.log.add("Пепельный ветер — трава недоступна.")
                    return
                ow.game.profile.inventory.add("grey_herb", 1, 20)
                self.clear_tile(tx, ty, layer)
                ow.game.audio.play_sfx("pickup")
                ow.log.add("Собрана серая трава.")
                self._notify_interact()
                return
            if ch == "+":
                ow.game.profile.inventory.add("root_fiber", 1, 20)
                self.clear_tile(tx, ty, layer)
                ow.game.audio.play_sfx("pickup")
                ow.log.add("Собрано корневое волокно.")
                self._notify_interact()
                return
            if ch == "*":
                ow.game.profile.inventory.add("star_shard", 1, 10)
                self.clear_tile(tx, ty, layer)
                ow.game.audio.play_sfx("pickup")
                ow.log.add("Найден осколок звезды.")
                self._notify_interact()
                return
            if ch == "$":
                ow.game.profile.inventory.add("ash_clump", 2, 30)
                ow.game.audio.play_sfx("pickup")
                ow.log.add("Подобран пепел.")
                self._notify_interact()
                return
            if ch == "&":
                ow.craft.open_station("forge")
                self._notify_interact()
                return
            if ch == "~":
                ow.craft.open_station("loom")
                self._notify_interact()
                return
            if ch == "@":
                self.open_dialogue("elder_intro")
                self._notify_interact()
                return
        if has_service(ow.game.world_state.companions, "mobile_forge"):
            cx, cy = companion_pos_for_player(px, py)
            if abs(cx - px) + abs(cy - py) <= 2:
                ow.craft.open_station("companion")
                self.open_dialogue("whisper_companion")
                self._notify_interact()
                return
        if "sorrow_companion" in ow.game.world_state.companions:
            ow.log.add("Осколки мерцают вдали...")

    def _notify_interact(self) -> None:
        tutorial = self.scene.game.tutorial
        if tutorial:
            tutorial.notify_interacted()

    def clear_tile(self, tx: int, ty: int, layer: str) -> None:
        ow = self.scene
        if layer == "dungeon":
            ow.game.world_map.set_dungeon_tile(tx, ty, ".")
        else:
            cx, cy, lx, ly = ow.game.world_map.world_to_chunk(tx, ty)
            chunk = ow.game.world_map.chunks.get((cx, cy))
            if chunk:
                chunk.set(lx, ly, ".")

    def open_dialogue(self, did: str) -> None:
        ow = self.scene
        ow.dialogue_id = did
        ow.dialogue.open(
            get_dialogue(did),
            voice_for_dialogue(did),
            get_dialogue_speaker(did),
        )
        ow.dialogue_open = True
        from src.i18n import t

        ow.log.add(t("ui.log.dialogue_advance"))

    def try_examine_world(self, wx: int, wy: int) -> None:
        ow = self.scene
        if (wx, wy) not in ow.visible:
            return
        if (wx, wy) == ow.player.tile_pos():
            ow.sheet.show()
            ow.sheet.bind_profile(ow.game.profile)
            if ow.game.tutorial:
                ow.game.tutorial.notify_sheet_opened()
            return
        from src.world.tile_entities import resolve_world_cell

        info = resolve_world_cell(wx, wy, ow.game.world_state.layer, ow.game)
        if info:
            _, art_id = info
            ow.examine.show(art_id)
            ow.game.audio.play_sfx("ui_examine")
            if ow.game.tutorial:
                ow.game.tutorial.notify_examine_opened()
