from collections import deque
from constants import IS_PASSABLE


def bfs(start: tuple[int, int], goal: tuple[int, int],
        map_data: list[list[int]], blocked=None) -> list[tuple[int, int]] | None:
    """Поиск пути на карте при помощи BFS."""
    if blocked is None:
        blocked = set()

    if start == goal:
        return [start]

    queue = deque([start])
    visited = {start}
    parents = {start: None}

    # Предполагаем, что map_data — это двумерный список [строка][столбец].
    height = len(map_data)
    width = len(map_data[0])

    while queue:
        cx, cy = queue.popleft()

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) == goal:
                    parents[(nx, ny)] = (cx, cy)
                    path = []
                    cur = goal
                    while cur is not None:
                        path.append(cur)
                        cur = parents[cur]
                    path.reverse()
                    return path

                if map_data[ny][nx] in IS_PASSABLE and (nx, ny) not in blocked:
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        parents[(nx, ny)] = (cx, cy)
                        queue.append((nx, ny))

    return None