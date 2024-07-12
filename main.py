import requests
import json
import random
import time
import math

HEADERS={'X-Auth-Token':'668d3dd517f68668d3dd517f6b'}
API_URL = "https://games-test.datsteam.dev/play/"

def registration():
    response = requests.put('https://games-test.datsteam.dev/play/zombidef/participate',headers=HEADERS)
    return(response)
def round_info():
    response = requests.get('https://games-test.datsteam.dev/rounds/zombidef',headers=HEADERS)
    json_data = response.json()
    return json_data
def around_info():
    try:
        response = requests.get("https://games-test.datsteam.dev/play/zombidef/units", headers=HEADERS)
        print
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching around_info: {e}")
        return None

def spot_info():
    try:
        response = requests.get("https://games-test.datsteam.dev/play/zombidef/world", headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching spot_info: {e}")
        return None

def step(actions):
    try:
        response = requests.post("https://games-test.datsteam.dev/play/zombidef/command", headers=HEADERS, json=actions)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending step: {e}")
        return None


def get_zombie_threat_score(zombie):
    """Определение угрозы от зомби по его типу и характеристикам."""
    threat_scores = {
        'normal': 1,
        'fast': 2,
        'bomber': 4,
        'liner': 6,
        'juggernaut': 5,
        'chaos_knight': 3
    }
    base_threat = threat_scores.get(zombie['type'], 0)
    return base_threat + (zombie['attack'] / 10)  # Учитываем силу атаки

def prioritize_zombies(zombies):
    """Сортировка зомби по уровню угрозы."""
    return sorted(zombies, key=get_zombie_threat_score, reverse=True)

def attack_zombies(base_coords, zombies):
    """Создание команд для атаки зомби с учетом их типа и угрозы."""
    attack_commands = []
    if base_coords and zombies:
        for base in base_coords:
            bx, by = base["x"], base["y"]
            base_id = base["id"]
            is_head = base.get("isHead", False)
            attack_range = 8 if is_head else 5
            
            prioritized_zombies = prioritize_zombies(zombies)
            for zombie in prioritized_zombies:
                zx, zy = zombie["x"], zombie["y"]
                zombie_type = zombie["type"]
                if calculate_distance(bx, by, zx, zy) <= attack_range:
                    if zombie_type == "normal" or zombie_type == "fast":
                        attack_commands.append({
                            "blockId": base_id,
                            "target": {"x": zx, "y": zy}
                        })
                    elif zombie_type == "bomber":
                        # Атака всех клеток в радиусе 1 от себя
                        for dx in range(-1, 2):
                            for dy in range(-1, 2):
                                if (dx != 0 or dy != 0) and 0 <= zx + dx < 10 and 0 <= zy + dy < 10:
                                    attack_commands.append({
                                        "blockId": base_id,
                                        "target": {"x": zx + dx, "y": zy + dy}
                                    })
                    elif zombie_type == "liner":
                        for x in range(zx, bx, -1):
                            if x == bx and zy == by:
                                attack_commands.append({
                                    "blockId": base_id,
                                    "target": {"x": x, "y": by}
                                })
                                break
                    elif zombie_type == "juggernaut":
                        attack_commands.append({
                            "blockId": base_id,
                            "target": {"x": zx, "y": zy}
                        })
                    elif zombie_type == "chaos_knight":
                        moves = [(2, 1), (2, -1), (-2, 1), (-2, -1),
                                 (1, 2), (1, -2), (-1, 2), (-1, -2)]
                        for dx, dy in moves:
                            nx, ny = zx + dx, zy + dy
                            if 0 <= nx < 10 and 0 <= ny < 10:
                                attack_commands.append({
                                    "blockId": base_id,
                                    "target": {"x": nx, "y": ny}
                                })
    return attack_commands


def move_base(base_coords):
    """Создание команды для перемещения базы в более безопасное место."""
    move_base_command = None
    if base_coords:
        # Перемещаем базу в более безопасное место, если здоровье базы низкое
        if base_coords[0]["health"] < 50:
            safe_spots = []
            for x in range(10):
                for y in range(10):
                    if (x, y) not in [(b["x"], b["y"]) for b in base_coords]:
                        safe_spots.append((x, y))
            if safe_spots:
                move_base_command = {
                    "x": safe_spots[random.randint(0, len(safe_spots) - 1)][0],
                    "y": safe_spots[random.randint(0, len(safe_spots) - 1)][1]
                }
    return move_base_command

def dynamic_strategy(base_coords, zombies, player_gold, spot_coords):
    """Определение стратегий на основе текущего состояния игры."""
    # Проверка угрозы зомби
    attack_commands = attack_zombies(base_coords, zombies)
    
    # Проверка возможности расширения базы
    build_commands = manage_base(base_coords, player_gold)
    
    # Проверка необходимости перемещения базы
    move_base_command = move_base(base_coords)
    
    return attack_commands, build_commands, move_base_command

def get_base_coords(base_data):
    """Получение координат всех блоков базы."""
    return [{'x': base['x'], 'y': base['y']} for base in base_data]

def get_buildable_spots(base_coords):
    """Определение доступных мест для расширения базы (клетки рядом с базой)."""
    buildable_spots = []
    occupied_coords = [(b['x'], b['y']) for b in base_coords]
    for base in base_coords:
        bx, by = base['x'], base['y']
        potential_coords = [(bx+1, by), (bx-1, by), (bx, by+1), (bx, by-1)]
        for cx, cy in potential_coords:
            if (cx, cy) not in occupied_coords:  # Проверка, что координаты не заняты
                buildable_spots.append((cx, cy))
                occupied_coords.append((cx, cy))  # Добавляем потенциальные координаты в список занятых
    return buildable_spots

def prioritize_spots(buildable_spots, base_coords):
    """Сортировка спотов для постройки на основе их расстояния от базы."""
    return sorted(buildable_spots, key=lambda spot: min(calculate_distance(spot[0], spot[1], b['x'], b['y']) for b in base_coords))

def calculate_distance(x1, y1, x2, y2):
    """Вычисление расстояния между двумя точками."""
    return ((x1 - x2)**2 + (y1 - y2)**2) ** 0.5

def prepare_build_commands(build_spots, player_gold):
    """Подготовка команд для постройки базы на основе отсортированных спотов."""
    build_commands = []
    # Построим максимум столько блоков, сколько позволяет золото
    build_cost = 1  # Замените на реальную стоимость постройки одного блока
    max_blocks = player_gold // build_cost
    
    for spot in build_spots:
        if max_blocks <= 0:
            break
        build_commands.append({"x": spot[0], "y": spot[1]})
        max_blocks -= 1
    return build_commands

def manage_base(base_coords, player_gold):
    """Управление постройкой базы: определение доступных мест и формирование команд."""
    buildable_spots = get_buildable_spots(base_coords)
    prioritized_spots = prioritize_spots(buildable_spots, base_coords)
    build_commands = prepare_build_commands(prioritized_spots, player_gold)
    return build_commands


def main():
    """Основной цикл игры."""
    while True:
        game_data = around_info()
        spot_data = spot_info()

        if game_data is None or spot_data is None:
            time.sleep(1)
            continue

        base_coords = game_data.get("base", [])
        zombies = game_data.get("zombies", [])
        player_gold = game_data["player"].get("gold", 0)
        turn_ends_in_ms = game_data.get("turnEndsInMs", 1000)
        spot_coords = [(spot["x"], spot["y"]) for spot in spot_data.get("zpots", [])]

        # Определение стратегий и подготовка команд
        attack_commands, build_commands, move_base_command = dynamic_strategy(base_coords, zombies, player_gold, spot_coords)

        # Отправка команд на сервер
        actions = {
            "attack": attack_commands,
            "build": build_commands,
            "moveBase": move_base_command
        }

        # Отладочная информация
        print(f"Attack Commands: {attack_commands}")
        print(f"Build Commands: {build_commands}")
        print(f"Move Base Command: {move_base_command}")

        step(actions)

        # Ожидание до следующего хода
        time.sleep(turn_ends_in_ms / 1000)

if __name__ == "__main__":
    main()