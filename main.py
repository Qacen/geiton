import requests
import json

import time
import math

HEADERS={'X-Auth-Token':'668d3dd517f68668d3dd517f6b'}
API_URL = "https://games-test.datsteam.dev/play/"


def round_info():
    response = requests.get('https://games-test.datsteam.dev/rounds/zombidef',headers=head)
    json_data = response.json()
    return json_data
def around_info():
    try:
        response = requests.get(f"{API_URL}zombidef/units", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching around_info: {e}")
        return None

def spot_info():
    try:
        response = requests.get(f"{API_URL}zombidef/world", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching spot_info: {e}")
        return None

def step(actions):
    try:
        response = requests.post(f"{API_URL}zombidef/command", headers=HEADERS, json=actions)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending step: {e}")
        return None


def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

def attack_zombies(base_coords, zombies):
    attack_commands = []
    if base_coords and zombies:
        for base in base_coords:
            bx, by = base["x"], base["y"]
            is_head = base.get("isHead", False)
            attack_range = 8 if is_head else 5
            attack_power = 40 if is_head else 10
            for zombie in zombies:
                zx, zy = zombie["x"], zombie["y"]
                if calculate_distance(bx, by, zx, zy) <= attack_range:
                    attack_commands.append({
                        "blockId": base["id"],
                        "target": {"x": zx, "y": zy}
                    })
    return attack_commands

def expand_base(player_gold, base_coords):
    build_commands = []
    if player_gold > 0 and base_coords:
        for base in base_coords:
            bx, by = base["x"], base["y"]
            potential_coords = [(bx+1, by), (bx-1, by), (bx, by+1), (bx, by-1)]
            for coord in potential_coords:
                if all(c["x"] != coord[0] or c["y"] != coord[1] for c in base_coords):
                    build_commands.append({"x": coord[0], "y": coord[1]})
                    player_gold -= 1
                if player_gold == 0:
                    break
            if player_gold == 0:
                break
    return build_commands

def main():
    while True:
        # Получение информации о текущем состоянии
        game_data = around_info()
        spot_data = spot_info()

        print(around_info.)

        if game_data is None or spot_data is None:
            time.sleep(1)
            continue

        base_coords = game_data.get("base", [])
        zombies = game_data.get("zombies", [])
        player_gold = game_data["player"].get("gold", 0)
        turn = game_data.get("turn", 0)
        turn_ends_in_ms = game_data.get("turnEndsInMs", 1000)

        # Подготовка команд для атаки
        attack_commands = attack_zombies(base_coords, zombies)

        # Подготовка команд для расширения базы
        build_commands = expand_base(player_gold, base_coords)

        # Подготовка команд для перемещения базы (пример перемещения в безопасную зону)
        move_base_command = None
        if base_coords and base_coords[0]["health"] < 50:
            move_base_command = {
                "x": base_coords[-1]["x"],
                "y": base_coords[-1]["y"]
            }

        # Отправка команд на сервер
        actions = {
            "attack": attack_commands,
            "build": build_commands,
            "moveBase": move_base_command
        }
        step(actions)
        # Ожидание до следующего хода
        time.sleep(turn_ends_in_ms / 1000)

if __name__ == "__main__":
    main()