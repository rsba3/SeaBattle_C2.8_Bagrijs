import random


class Point:

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y

    def __repr__(self) -> str:
       return f"({self.x}, {self.y})"


class Ship:
    def __init__(self, bow: Point, length: int, direction: int):
        self.bow = bow  # начальная точка (нос корабля)
        self.length = length  # длина корабля в клетках
        self.direction = direction  # направление (0 - горизонтальное, 1 - вертикальное)
        self.lives = length  # количество жизней корабля (равно его длине)

    @property
    def points(self) -> list[Point]:
        ship_points = []
        for i in range(self.length):
            # Вычисляем координаты каждой точки корабля в зависимости от направления
            cur_x = self.bow.x + i * (self.direction == 1)
            cur_y = self.bow.y + i * (self.direction == 0)
            ship_points.append(Point(cur_x, cur_y))
        return ship_points

    def hit(self, shot: Point) -> bool:
        return shot in self.points


class BoardException(Exception):
    pass


class BoardOutException(BoardException):
    def __str__(self) -> str:
        return "Вы пытаетесь выстрелить за доску!"


class BoardUsedException(BoardException):
   def __str__(self) -> str:
        return "Вы уже стреляли в эту клетку!"


class BoardWrongShipException(BoardException):
    pass


class Board:
    def __init__(self, size: int = 6, hidden: bool = False):
        self.size = size  # размер доски
        self.field = [["O"] * size for _ in range(size)]  # двумерный массив для хранения состояния поля
        self.busy = []  # список занятых точек
        self.ships = []  # список кораблей на доске
        self.shots = []  # список точек, куда уже стреляли
        self.hidden = hidden  # скрыты ли корабли (используется для доски компьютера)

    def add_ship(self, ship: Ship) -> None:
        for p in ship.points:
            if self.out(p) or p in self.busy:
                raise BoardWrongShipException()
        for p in ship.points:
            self.field[p.x][p.y] = "■"
            self.busy.append(p)

        self.ships.append(ship)
        self.contour(ship)

    def contour(self, ship: Ship, verb: bool = False) -> None:
        near = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 0), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        for p in ship.points:
            for dx, dy in near:
                cur = Point(p.x + dx, p.y + dy)
                if not self.out(cur) and cur not in self.busy:
                    if verb:
                        self.field[cur.x][cur.y] = "."
                    self.busy.append(cur)

    def out(self, p: Point) -> bool:
        return not (0 <= p.x < self.size and 0 <= p.y < self.size)

    def shot(self, p: Point) -> bool:
        if self.out(p):
            raise BoardOutException()

        if p in self.shots:
            raise BoardUsedException()

        self.shots.append(p)

        for ship in self.ships:
            if ship.hit(p):
                ship.lives -= 1
                self.field[p.x][p.y] = "X"  # помечаем попадание
                if ship.lives == 0:
                    self.contour(ship, verb=True)  # обводим контур вокруг уничтоженного корабля
                    print("Корабль уничтожен!")
                else:
                    print("Корабль ранен!")
                return True

        self.field[p.x][p.y] = "T"  # помечаем промах
        print("Мимо!")
        return False

    def begin(self) -> None:
        self.busy = []

    def __str__(self) -> str:
        res = ""
        res += "  | 1 | 2 | 3 | 4 | 5 | 6 |"
        for i, row in enumerate(self.field):
            res += f"\n{i + 1} | "
            for j in row:
                # Скрываем корабли на доске компьютера
                if self.hidden and j == "■":
                    res += "O | "
                else:
                    res += f"{j} | "
        return res

    def defeat(self) -> bool:
        return all(ship.lives == 0 for ship in self.ships)


class Player:
    def __init__(self, board: Board, enemy: Board):
        self.board = board
        self.enemy = enemy

    def ask(self) -> Point:
        raise NotImplementedError()

    def move(self) -> bool:
        while True:
            try:
                target = self.ask()  # запрос точки выстрела
                repeat = self.enemy.shot(target)  # выстрел по доске противника
                return repeat  # возвращаем True, если выстрел попал, иначе False
            except BoardException as e:
                print(e)  # выводим сообщение об ошибке и повторяем попытку


class AI(Player):
    def ask(self) -> Point:
        while True:
            p = Point(random.randint(0, 5), random.randint(0, 5))
            if p not in self.enemy.shots:  # проверяем, что в эту точку еще не стреляли
                print(f"Ход компьютера: {p.x + 1} {p.y + 1}")
                return p


class User(Player):
    def ask(self) -> Point:
        while True:
            coords = input("Ваш ход: ").split()  # запрос координат у пользователя
            if len(coords) != 2:
                print(" Введите 2 координаты! ")
                continue

            x, y = coords

            if not x.isdigit() or not y.isdigit():
                print(" Введите числа! ")
                continue

            x, y = int(x), int(y)

            return Point(x - 1, y - 1)  # преобразуем ввод в координаты (0-based индекс)


class Game:
    def __init__(self, size: int = 6):
        self.size = size
        pl = self.random_board()  # создание доски пользователя
        co = self.random_board()  # создание доски компьютера
        co.hidden = True  # скрываем доску компьютера

        self.ai = AI(co, pl)  # ИИ играет с доской компьютера и атакует доску пользователя
        self.us = User(pl, co)  # пользователь играет с доской пользователя и атакует доску компьютера

    def try_board(self) -> Board:
        lens = [3, 2, 2, 1, 1, 1, 1]  # размеры кораблей
        board = Board(size=self.size)
        attempts = 0
        for l in lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None  # возвращаем None, если слишком много неудачных попыток
                ship = Ship(Point(random.randint(0, self.size - 1), random.randint(0, self.size - 1)), l,
                            random.randint(0, 1))
                try:
                    board.add_ship(ship)  # пытаемся разместить корабль на доске
                    break
                except BoardWrongShipException:
                    pass
        board.begin()
        return board

    def random_board(self) -> Board:
        board = None
        while board is None:
            board = self.try_board()  # продолжаем пытаться создать доску, пока не получится
        return board

    def greet(self) -> None:
        print("-------------------")
        print("  Приветсвуем вас  ")
        print("      в игре       ")
        print("    морской бой    ")
        print("-------------------")
        print(" формат ввода: x y ")
        print(" x - номер строки  ")
        print(" y - номер столбца ")

    def loop(self) -> None:
        num = 0  # номер текущего хода
        while True:
            print("-" * 20)
            print("Доска пользователя:")
            print(self.us.board)
            print("-" * 20)
            print("Доска компьютера:")
            print(self.ai.board)
            if num % 2 == 0:
                print("-" * 20)
                print("Ходит пользователь!")
                repeat = self.us.move()  # ход пользователя
            else:
                print("-" * 20)
                print("Ходит компьютер!")
                repeat = self.ai.move()  # ход компьютера
            if repeat:
                num -= 1  # если был удачный выстрел, ход повторяется

            if self.ai.board.defeat():
                print("-" * 20)
                print("Пользователь выиграл!")
                break

            if self.us.board.defeat():
                print("-" * 20)
                print("Компьютер выиграл!")
                break
            num += 1

    def start(self) -> None:
        self.greet()
        self.loop()


if __name__ == "__main__":
    game = Game()
    game.start()
