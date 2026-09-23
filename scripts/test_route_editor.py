#!/usr/bin/env python3
"""
Headless check of the edit-route editor: the clicks and keys really are wired,
and every edit keeps a valid tour with a correctly recomputed latency.

Events go through the canvas the same way a real mouse does
(canvas.callbacks.process with pixel coordinates), not by calling the handlers
directly -- otherwise it would not catch the bug it was written for: matplotlib
keeps only a WEAK reference to callbacks, so an editor nobody holds a reference
to is garbage collected and every handler silently stops firing.

    python3 scripts/test_route_editor.py
"""
import gc
import os
import sys

os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
from matplotlib.backend_bases import KeyEvent, MouseEvent

import instance_visualizer as viz

failures = []


def check(label, condition, detail=""):
    print(f"  {'ok  ' if condition else 'FAIL'} {label}{'   ' + detail if detail else ''}")
    if not condition:
        failures.append(label)


def main():
    inst = viz.load_instance("eil51.tsp")
    route = viz.load_route(inst, from_best=True)
    n = len(inst["coords"])

    ed = viz.RouteEditor(inst, route)
    ed.fig.canvas.draw()
    gc.collect()

    print("handlers survive garbage collection")
    cbs = ed.fig.canvas.callbacks.callbacks
    for event, name in [("button_press_event", "on_click"),
                        ("key_press_event", "on_key"),
                        ("motion_notify_event", "on_hover")]:
        alive = any(name in str(ref()) for ref in cbs.get(event, {}).values()
                    if ref() is not None)
        check(f"{event} -> {name}", alive)

    def click(city):
        x, y = ed.ax.transData.transform(inst["coords"][city])
        ed.fig.canvas.callbacks.process(
            "button_press_event", MouseEvent("button_press_event", ed.fig.canvas, x, y, 1))

    def key(k):
        ed.fig.canvas.callbacks.process(
            "key_press_event", KeyEvent("key_press_event", ed.fig.canvas, k))

    def latency():
        return viz.arrival_times(inst, ed.route)[1]

    def valid():
        return sorted(ed.route) == list(range(n)) and ed.route[0] == inst["depot"]

    start = latency()
    print(f"\nedits, starting from latency {start}")

    click(ed.route[3])
    check("first click picks a city up", ed.picked is not None, f"city {ed.picked}")
    click(ed.route[20])
    moved = latency()
    check("second click applies the move", moved != start and valid(), f"latency {moved}")

    key("u")
    check("u undoes", latency() == start and valid())

    key("s")
    check("s switches to swap", ed.mode == "s")
    click(ed.route[5]); click(ed.route[9])
    check("swap applies", latency() != start and valid(), f"latency {latency()}")

    key("r")
    check("r switches to reverse", ed.mode == "r")
    before = latency()
    click(ed.route[5]); click(ed.route[15])
    check("reverse applies", latency() != before and valid(), f"latency {latency()}")

    key("z")
    check("z restores the original", latency() == start and valid())

    ed.mode = "m"
    ed.apply(ed.route[0], ed.route[7])
    check("the depot cannot be moved", ed.route[0] == inst["depot"] and latency() == start)

    print("\nhover")
    city = ed.route[25]
    ev = MouseEvent("motion_notify_event", ed.fig.canvas,
                    *ed.ax.transData.transform(inst["coords"][city]))
    ed.fig.canvas.callbacks.process("motion_notify_event", ev)
    text = ed.tip.get_text()
    check("tooltip shows the city", f"cidade {city}" in text)
    check("tooltip shows its arrival time",
          str(ed.arrival[ed.pos_of(city)]).replace(",", " ") in text.replace(",", " "),
          repr(text.replace(chr(10), " | ")))

    print("\nlatency agrees with the tracked solution")
    check("eil51 route from best_solutions recomputes to its own cost",
          viz.arrival_times(inst, viz.load_route(inst, from_best=True))[1] == start,
          f"{start}")

    plt.close("all")
    print("\n" + ("PASS" if not failures else f"FAIL ({len(failures)})"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
