import time
import pymem
import requests


class CHEATS:
    def __init__(self, pm, client):
        self.pm = pm
        self.client = client

        offsets = requests.get('https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json').json()
        client_dll = requests.get('https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json').json()

        self.dwEntityList = offsets['client.dll']['dwEntityList']
        self.dwLocalPlayerPawn = offsets['client.dll']['dwLocalPlayerPawn']

        self.m_iTeamNum = int(client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum'])
        self.m_hPlayerPawn = client_dll['client.dll']['classes']['CCSPlayerController']['fields']['m_hPlayerPawn']
        self.m_flFlashDuration = client_dll['client.dll']['classes']['C_CSPlayerPawnBase']['fields']['m_flFlashDuration']
        self.m_lifeState = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_lifeState']
        self.m_iHealth = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
        self.m_Glow = client_dll['client.dll']['classes']['C_BaseModelEntity']['fields']['m_Glow']
        self.m_bGlowing = client_dll['client.dll']['classes']['CGlowProperty']['fields']['m_bGlowing']
        self.m_glowColorOverride = client_dll['client.dll']['classes']['CGlowProperty']['fields']['m_glowColorOverride']
        self.m_iGlowType = client_dll['client.dll']['classes']['CGlowProperty']['fields']['m_iGlowType']

    def _get_entity_pawns(self) -> list[int]:
        pawns = []
        entity_list_base = self.pm.read_longlong(self.client + self.dwEntityList)
        for i in range(1, 64):
            list_entry = self.pm.read_longlong(entity_list_base + ((8 * (i & 0x7FFF) >> 9) + 16))
            if not list_entry:
                continue
            entity_controller = self.pm.read_longlong(list_entry + 112 * (i & 0x1FF))
            if not entity_controller:
                continue
            controller_pawn_handle = self.pm.read_int(entity_controller + self.m_hPlayerPawn)
            if not controller_pawn_handle:
                continue
            pawn_entry = self.pm.read_longlong(entity_list_base + (0x8 * ((controller_pawn_handle & 0x7FFF) >> 9) + 16))
            if not pawn_entry:
                continue
            entity_pawn = self.pm.read_longlong(pawn_entry + 112 * (controller_pawn_handle & 0x1FF))
            if entity_pawn:
                pawns.append(entity_pawn)
        return pawns

    def _get_health_color(self, health: int) -> int:
        health = max(0, min(health, 100))
        r = int(255 * (1 - health / 100))
        g = int(255 * (health / 100))
        b = 0
        a = 180
        return (a << 24) | (b << 16) | (g << 8) | r

    def esp_glow(self, enabled=True):
        while enabled:
            try:
                local_player = self.pm.read_longlong(self.client + self.dwLocalPlayerPawn)
                if not local_player:
                    time.sleep(0.1)
                    continue

                local_team = self.pm.read_int(local_player + self.m_iTeamNum)
                pawns = self._get_entity_pawns()

                for entity_pawn in pawns:
                    if not entity_pawn:
                        continue

                    life_state = self.pm.read_int(entity_pawn + self.m_lifeState)
                    if life_state != 256:
                        continue

                    if self.pm.read_int(entity_pawn + self.m_iTeamNum) == local_team:
                        continue

                    health = self.pm.read_int(entity_pawn + self.m_iHealth)
                    color_argb = self._get_health_color(health)

                    glow = entity_pawn + self.m_Glow
                    self.pm.write_int(glow + self.m_glowColorOverride, color_argb)
                    self.pm.write_bool(glow + self.m_bGlowing, True)
                    self.pm.write_int(glow + self.m_iGlowType, 4)

                time.sleep(0.01)
            except Exception as e:
                print(f"ESP error: {e}")
                time.sleep(1)

    def anti_flash(self, enabled=True):
        while enabled:
            try:
                local_player = self.pm.read_longlong(self.client + self.dwLocalPlayerPawn)
                if not local_player:
                    time.sleep(0.05)
                    continue

                flash_dur = self.pm.read_float(local_player + self.m_flFlashDuration)
                if flash_dur > 0:
                    self.pm.write_float(local_player + self.m_flFlashDuration, 0.0)

                time.sleep(0.05)
            except Exception as e:
                print(f"Anti-flash error: {e}")
                time.sleep(0.5)


if __name__ == '__main__':
    while True:
        try:
            pm = pymem.Pymem("cs2.exe")
            client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
            break
        except:
            time.sleep(1)
            continue

    #Logo
    print(r"""
    ██╗    ██╗ █████╗ ██╗  ██╗ ██████╗██╗  ██╗███████╗ █████╗ ████████╗███████╗
    ██║    ██║██╔══██╗╚██╗██╔╝██╔════╝██║  ██║██╔════╝██╔══██╗╚══██╔══╝██╔════╝
    ██║ █╗ ██║███████║ ╚███╔╝ ██║     ███████║█████╗  ███████║   ██║   ███████╗
    ██║███╗██║██╔══██║ ██╔██╗ ██║     ██╔══██║██╔══╝  ██╔══██║   ██║   ╚════██║
    ╚███╔███╔╝██║  ██║██╔╝ ██╗╚██████╗██║  ██║███████╗██║  ██║   ██║   ███████║
     ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
    """)

    print("Made by Waxby")

    cheats = CHEATS(pm, client)

    import threading
    threading.Thread(target=cheats.esp_glow, daemon=True).start()
    cheats.anti_flash()