import requests
import json
import random
import time
import math
import matplotlib.pyplot as plt
from collections import deque 


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

def calculate_distance(x1, y1, x2, y2):
    """Вычисление расстояния между двумя точками."""
    return ((x1 - x2)**2 + (y1 - y2)**2) ** 0.5

def get_zombie_threat_score(zombie):
    """Определение угрозы от зомби по его типу и характеристикам."""
    threat_scores = {
        'normal': 1,
        'fast': 2,
        'bomber': 5,
        'liner': 20,
        'juggernaut': 7,
        'chaos_knight': 3
    }
    base_threat = threat_scores.get(zombie['type'], 0)
    return base_threat + (zombie['attack'] / 10)  # Учитываем силу атаки

def prioritize_zombies(zombies):
    """Сортировка зомби по уровню угрозы."""
    return sorted(zombies, key=get_zombie_threat_score, reverse=True)

def prioritize_enemy_blocks(enemy_blocks):
    """Сортировка вражеских блоков по приоритету атаки."""
    if enemy_blocks:
        return sorted(enemy_blocks, key=lambda block: (block.get('isHead', False), -block['health']))
    return []

def attack_targets(base_coords, zombies, enemy_blocks):
    """Создание команд для атаки зомби и вражеских блоков."""
    attack_commands = []

    prioritized_zombies = prioritize_zombies(zombies)
    prioritized_enemy_blocks = prioritize_enemy_blocks(enemy_blocks)

    if base_coords:
        for base in base_coords:
            bx, by = base["x"], base["y"]
            base_id = base["id"]
            is_head = base.get("isHead", False)
            attack_range = 8 if is_head else 5

            for zombie in prioritized_zombies:
                zx, zy = zombie["x"], zombie["y"]
                if calculate_distance(bx, by, zx, zy) <= attack_range:
                    attack_commands.append({
                        "blockId": base_id,
                        "target": {"x": zx, "y": zy}
                    })

            for enemy_block in prioritized_enemy_blocks:
                ex, ey = enemy_block["x"], enemy_block["y"]
                if calculate_distance(bx, by, ex, ey) <= attack_range:
                    attack_commands.append({
                        "blockId": base_id,
                        "target": {"x": ex, "y": ey}
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

def dynamic_strategy(base_coords, zombies, player_gold, enemy_blocks, width, height, spots):
    """Определение стратегий на основе текущего состояния игры."""
    # Проверка угрозы зомби и вражеских блоков
    attack_commands = attack_targets(base_coords, zombies, enemy_blocks)

    build_commands = manage_base(base_coords, player_gold)
    print(build_commands)
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
    build_cost = 10  # Замените на реальную стоимость постройки одного блока
    max_blocks = player_gold // build_cost
    
    for spot in build_spots:
        if max_blocks <= 0:
            break
        build_commands.append({"x": spot[0], "y": spot[1]})
        max_blocks -= 1
    return build_commands

def get_zspot_coords(spot_data):
    """Получение координат точек спауна зомби типа 'default'."""
    return [(spot['x'], spot['y']) for spot in spot_data if spot['type'] == 'default']

def prioritize_spots_with_zspot(buildable_spots, zspot_coords):
    """Сортировка спотов для постройки на основе их расстояния до точек спауна зомби типа 'default'."""
    return sorted(buildable_spots, key=lambda spot: min(calculate_distance(spot[0], spot[1], zx, zy) for (zx, zy) in zspot_coords))

def manage_base(base_coords, player_gold, zspot_coords):
    """Управление постройкой базы: определение доступных мест и формирование команд с учетом точек спауна зомби типа 'default'."""
    buildable_spots = get_buildable_spots(base_coords)
    prioritized_spots = prioritize_spots_with_zspot(buildable_spots, zspot_coords)
    build_commands = prepare_build_commands(prioritized_spots, player_gold)
    return build_commands

def visualize_base(base_coords, spots, zombies, enemy_blocks, width, height):
    """Визуализация структуры базы на графике с динамическими размерами."""
    print('visualizat')
    plt.figure(figsize=(width, height))
    plt.xlim(0, width)
    plt.ylim(0, height)
    plt.gca().set_aspect('equal', adjustable='box')

    for base in base_coords:
        plt.plot(base['x'], base['y'], 'bs', label='Base Block' if base['isHead'] else '_nolegend_')
    
    for spot in spots:
        if spot['type'] == 'default':
            plt.plot(spot['x'], spot['y'], 'ro', label='Zombie Spawner')
        elif spot['type'] == 'wall':
            plt.plot(spot['x'], spot['y'], 'go', label='Wall')

    for zombie in zombies:
        plt.plot(zombie['x'], zombie['y'], 'k*', label='Zombie')

    for block in enemy_blocks:
        plt.plot(block['x'], block['y'], 'rs', label='Enemy Block')

    plt.legend(loc='upper right')
    plt.grid(True)
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Base Visualization')
    plt.show()

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
        enemy_blocks = game_data.get("enemyBlocks", [])
        player_gold = game_data["player"].get("gold", 0)
        turn_ends_in_ms = game_data.get("turnEndsInMs", 1000)
        zspot_coords = get_zspot_coords(spot_data['zpots'])  # Получаем координаты точек спауна зомби типа 'default'
        spot_coords = [(spot["x"], spot["y"]) for spot in spot_data.get("spots", [])]
        width = max(x for x, y in spot_coords) + 1 if spot_coords else 10
        height = max(y for x, y in spot_coords) + 1 if spot_coords else 10

        # Определение стратегий и подготовка команд
        attack_commands, build_commands, move_base_command = dynamic_strategy(base_coords, zombies, player_gold, enemy_blocks, width, height, spot_data)

        # Обновление функции управления базой с учетом точек спауна зомби
        build_commands = manage_base(base_coords, player_gold, zspot_coords)

        # Подготовка команд для отправки на сервер
        actions = {
            "attack": attack_commands,
            "build": build_commands,
            "moveBase": move_base_command
        }

        # Отладочная информация
        print(f"Attack Commands: {len(attack_commands)}")
        print(f"Build Commands: {build_commands}")
        print(f"Move Base Command: {move_base_command}")

        step(actions)

        if random.randrange(1, 3) == 3:
            try:
                visualize_base(base_coords, spot_data.get("spots", []), zombies, enemy_blocks, width, height)
            except:
                print('Error visualizing base')
        
        # Ожидание до следующего хода
        time.sleep(turn_ends_in_ms / 1000)

if __name__ == "__main__":
    # while True:
    #     print(registration().text)
    #     time.sleep(10)
    main()
