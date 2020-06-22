#!/usr/bin/python3
import argparse
from itertools import product
from multiprocessing import Pool, Manager
from collections import namedtuple
from queue import Empty

from ortools.sat.python import cp_model

Rectangle = namedtuple(
    "Rectangle",
    ['xl', 'yb', 'xr', 'yt'],
    defaults=(None,) * 4
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("colors", type=int, help="The number of colors to use")
    return parser.parse_args().colors


def gen_grid_dims(rect):
    xl, yb, xr, yt = rect
    print(
        "Starting a generator with the following bounds: ",
        f"{xl}, {yb}, {xr}, {yt}"
    )
    if (xr and xl + 1 >= xr) or (yt and yb + 1 >= yt):
        return
    # don't search past boundaries
    x = xl + 1
    # rightmost x
    while (
        (xr is None or x < xr)
    ):
        y = yb + 1
        # topmost y or symm line
        while ((yt and y < yt) or (yt is None and x >= y)):
            split_msg = (yield (x, y))
            if split_msg:
                # kill this iterator, return new ones
                # get quads UL and BR
                yield (
                    Rectangle(max(xl, y), y, x, min(yt, x) if yt else None),
                    Rectangle(x, yb, xr, y)
                )
                return

            y += 1
        x += 1


def run_sat_solver_for_size(colors, xbound, ybound):
    model = cp_model.CpModel()
    rectangle = [
        [
            model.NewIntVar(0, colors-1, f"ind{x}{y}")
            for y in range(ybound)
        ]
        for x in range(xbound)
    ]

    # create column-wise contraints for each row
    half_color = []
    for row in rectangle:
        row1 = []
        for (ind, col1) in enumerate(row[:-1]):
            row2 = []
            for col2 in row[col1+1:]:
                row2.append(...)
            row1.append(row2)
        half_color.append(row1)


def format_coloring(coloring):
    return None


def search_for_obs_set(
        obs_queue,
        gen_queue,
        colors,
):
    while True:
        bounds, sub_colorings = gen_queue.get()
        generator = gen_grid_dims(bounds)

        def has_sub_coloring(x, y):
            if y > x:
                return has_sub_coloring(y, x)
            return x == bounds.xl or y == bounds.yb or (x, y) in sub_colorings

        for x, y in generator:
            print(sub_colorings)
            print(f"x: {x}, y: {y}")
            coloring = run_sat_solver_for_size(colors, x, y)
            if not coloring:
                print(f"{x}, {y} has no coloring")
                if has_sub_coloring(x-1, y) and has_sub_coloring(x, y-1):
                    print(f"{x}, {y} is an obstruction set member")
                    obs_queue.put(Rectangle(0, 0, x, y))
                    (UL, BR) = generator.send(True)  # splitting time
                    print("created ", UL, " and ", BR)
                    gen_queue.put((UL, sub_colorings))
                    gen_queue.put((BR, sub_colorings))
                else:
                    sub_colorings.add((x, y))
            else:
                print(
                    f"{x}, {y} has the following coloring:",
                    format_coloring(coloring)
                )
                sub_colorings.add((x, y))
        print("finishing generator", generator)
        gen_queue.task_done()


def main():
    colors = parse_args()
    with Manager() as manager:
        obs_queue = manager.Queue()
        gen_queue = manager.Queue()
        gen_queue.put((Rectangle(colors, colors), set()))

        with Pool(1, search_for_obs_set, (obs_queue, gen_queue, colors)) as _:
            gen_queue.join()

            print(
                "Obstruction set members",
                "-----------------------",
                sep='\n'
            )
            while True:
                try:
                    print(obs_queue.get_nowait())
                except Empty:
                    break


if __name__ == "__main__":
    main()
