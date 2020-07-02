#!/usr/bin/env python3
from ortools.sat.python import cp_model
from collections import namedtuple
from itertools import product, combinations
from typing import Generator
from termcolor import colored
import argparse

Rectangle = namedtuple(
    "Rectangle",
    ['xl', 'yb', 'xr', 'yt'],
    defaults=(None,) * 4
)


def rectangle_with_color(solver, intvars):
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

    rectangle = []
    for row in intvars:
        colored_row = []
        for entry in row:
            test = solver.Value(entry)
            if test < len(rectangle_with_color.colors):
                colored_row.append(colored(
                    "●",
                    color=rectangle_with_color.colors[test])
                )
            else:
                colored_row.append(test)
        rectangle.append(colored_row)

    return rectangle


def print_rectangle(colored_rectangle):
    if not colored_rectangle:
        print("Not a colorable rectangle")
    for row in colored_rectangle:
        print(*row, sep=" ", end="\n")


def sub_rectangles(rect: Rectangle) -> Generator[Rectangle, None, None]:
    for (xl, xr), (yb, yt) in product(
            combinations(range(rect.xl, rect.xr), 2),
            combinations(range(rect.yb, rect.yt), 2),
            ):
        yield Rectangle(xl, yb, xr, yt)


def is_colorable(rect: Rectangle, ncolors: int) -> bool:
    # create big array of all colors and indices
    model = cp_model.CpModel()
    intvars = [
        [
            model.NewIntVar(0, ncolors-1, f"{x},{y}")
            for x in range(rect.xl, rect.xr)
        ]
        for y in range(rect.yb, rect.yt)
    ]

    # first parameter is y, second parameter is x
    col_bindings = []
    for row_idx, row in enumerate(intvars):
        row_binding = {}  # just easier
        for (col1idx, col1), (col2idx, col2) in combinations(
                enumerate(row), 2
        ):
            temp = model.NewBoolVar(f"{row_idx},{col1idx},{col2idx}")
            model.Add(
                intvars[row_idx][col1idx] == intvars[row_idx][col2idx]
            ).OnlyEnforceIf(temp)
            model.Add(
                intvars[row_idx][col1idx] != intvars[row_idx][col2idx]
            ).OnlyEnforceIf(temp.Not())
            row_binding[(col1idx, col2idx)] = temp
        col_bindings.append(row_binding)

    # first parameter is x, second parameter is y
    row_bindings = [dict() for i in range(len(intvars[0]))]
    for (idx1, row1), (idx2, row2) in combinations(enumerate(intvars), 2):
        for idx, (col_entry1, col_entry2) in enumerate(zip(row1, row)):
            temp = model.NewBoolVar(f"{idx},{idx1},{idx2}")
            model.Add(
                intvars[idx1][idx] == intvars[idx2][idx]
            ).OnlyEnforceIf(temp)
            model.Add(
                intvars[idx1][idx] != intvars[idx2][idx]
            ).OnlyEnforceIf(temp.Not())
            row_bindings[idx][(idx1, idx2)] = temp

    # now state that if L and T are equal, B must not be.
    for xl, yb, xr, yt in sub_rectangles(rect):
        model.AddBoolOr([
            row_bindings[xl][(yb, yt)].Not(),
            row_bindings[xr][(yb, yt)].Not(),
            col_bindings[yb][(xl, xr)].Not(),
            col_bindings[yt][(xl, xr)].Not()
        ])

    solver = cp_model.CpSolver()
    was_successful = solver.Solve(model) in [
        cp_model.FEASIBLE, cp_model.OPTIMAL
    ]

    if was_successful:
        return rectangle_with_color(solver, intvars)
    else:
        return None


def buildRectangle(arg: str) -> Rectangle:
    raw_parts = arg.split("x")
    if len(raw_parts) != 2:
        raise argparse.ArgumentTypeError("Width and height must be given, deliminated by an \"x\"")

    try:
        return Rectangle(0, 0, int(raw_parts[0]), int(raw_parts[1]))
    except ValueError:
        raise argparse.ArgumentTypeError("Width and height must be integers")

        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dim",
        help="width x height i.e. 18x18",
        type=buildRectangle
    )
    parser.add_argument(
        "colors",
        help="Give the desired number of colors to use",
        type=int
    )
    args = parser.parse_args()

    print_rectangle(is_colorable(args.dim, args.colors))
