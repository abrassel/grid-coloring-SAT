from ortools.sat.python import cp_model
from collections import namedtuple
from itertools import product, combinations
from typing import Generator
from termcolor import colored

Rect = namedtuple('Rect', ['xl', 'xr', 'yl', 'yr'])


def rectangle_with_color(solver, boolvars):
    rectangle_with_color.colors = [
        "red",
        "green",
        "blue",
        "white",
        "magenta",
        "yellow",
        "cyan",
        "grey"
    ]

    color_flag = len(boolvars[0][0]) <= len(rectangle_with_color.colors)

    rectangle = []
    for row in boolvars:
        colored_row = []
        for entry in row:
            for c, c_var in enumerate(entry):
                if solver.BooleanValue(c_var):
                    if color_flag:
                        colored_row.append(colored(
                            "●",
                            color=rectangle_with_color.colors[c])
                        )
                    else:
                        colored_row.append(c)
                    break
                return None  # not solvable
        rectangle.append(colored_row)

    return rectangle


def print_rectangle(colored_rectangle):
    if not colored_rectangle:
        print("Not a colorable rectangle")
    for row in colored_rectangle:
        print(*row, sep=" ", end="\n")


def sub_rectangles(rect: Rect) -> Generator[Rect, None, None]:
    for (xl, xr), (yl, yr) in product(
            combinations(range(rect.xl, rect.xr), 2),
            combinations(range(rect.yl, rect.yr), 2),
            ):
        yield Rect(xl, xr, yl, yr)


def is_colorable(rect: Rect, ncolors: int) -> bool:
    # create big array of all colors and indices
    model = cp_model.CpModel()
    boolvars = [
        [
            [
                model.NewBoolVar(f"{x},{y},{c}")
                for c in range(ncolors)
            ]
            for y in range(rect.yl, rect.yr)
        ]
        for x in range(rect.xl, rect.xr)
    ]

    # add edge case for only 1 assignment
    for row in boolvars:
        for cell in row:
            model.AddBoolXOr(cell)

    # assert not all equal for all rectangles
    for xl, xr, yl, yr in sub_rectangles(rect):
        for c in range(ncolors):
            model.AddBoolOr([
                boolvars[xl][yl][c].Not(),
                boolvars[xl][yr][c].Not(),
                boolvars[xr][yl][c].Not(),
                boolvars[xr][yr][c].Not(),
            ])

    solver = cp_model.CpSolver()
    was_successful = solver.Solve(model) in [
        cp_model.FEASIBLE, cp_model.OPTIMAL
    ]

    if was_successful:
        return rectangle_with_color(solver, boolvars)
    else:
        return None
