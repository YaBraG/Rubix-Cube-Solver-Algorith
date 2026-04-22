"""Tkinter desktop app for manual and camera-assisted cube solving."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import StringVar, Tk, messagebox
from tkinter import ttk

from .gui_models import (
    DISPLAY_COLORS,
    DISPLAY_LETTERS,
    EDITABLE_INDEXES,
    TEXT_COLORS,
    clone_faces,
    count_editor_colors,
    create_empty_editor_faces,
    inject_virtual_centers,
    load_editor_faces_from_session,
)
from .gui_solver import solve_editor_faces
from .motor_serial import MotorSerialError, list_serial_ports, ping_arduino_port, send_commands_on_port


APP_TITLE = "Rubik's Cube Solver App"
PALETTE_COLORS = ["white", "yellow", "green", "blue", "red", "orange", "unknown"]
COLOR_SHORTCUTS = {
    "w": "white",
    "y": "yellow",
    "g": "green",
    "b": "blue",
    "r": "red",
    "o": "orange",
    "u": "unknown",
    "1": "white",
    "2": "yellow",
    "3": "green",
    "4": "blue",
    "5": "red",
    "6": "orange",
    "7": "unknown",
}
SHORTCUT_LABELS = {
    "white": "W/1 White",
    "yellow": "Y/2 Yellow",
    "green": "G/3 Green",
    "blue": "B/4 Blue",
    "red": "R/5 Red",
    "orange": "O/6 Orange",
    "unknown": "U/7 Unknown",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rubiks-gui-app",
        description="Launch the Tkinter desktop app for manual and camera-assisted solving.",
    )
    return parser


def compute_window_geometry(screen_width: int, screen_height: int) -> tuple[str, tuple[int, int]]:
    width = max(980, min(int(screen_width * 0.9), 1500))
    height = max(700, min(int(screen_height * 0.9), 980))
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 3)
    return f"{width}x{height}+{x}+{y}", (900, 640)


def resolve_color_shortcut(key: str) -> str | None:
    return COLOR_SHORTCUTS.get(key.lower())


def get_popup_color_options() -> list[str]:
    return PALETTE_COLORS.copy()


def build_scanner_log_path(session_dir: str | Path) -> Path:
    return Path(session_dir) / "scanner_log.txt"


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent: ttk.Frame, *, horizontal: bool = False) -> None:
        super().__init__(parent)
        self.allow_horizontal = horizontal
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.v_scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)

        self.h_scrollbar: ttk.Scrollbar | None = None
        if horizontal:
            self.h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
            self.h_scrollbar.pack(side="bottom", fill="x")
            self.canvas.configure(xscrollcommand=self.h_scrollbar.set)

        self.content = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_content_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        if not self.allow_horizontal:
            self.canvas.itemconfigure(self.window_id, width=event.width)


class RubiksGuiApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        geometry, min_size = compute_window_geometry(screen_width, screen_height)
        self.root.geometry(geometry)
        self.root.minsize(*min_size)

        self.current_mode = "manual"
        self.selected_color = StringVar(value="white")
        self.status_var = StringVar(value="Choose Manual or Camera Scan.")
        self.editor_note_var = StringVar(value="Centers are virtual and fixed.")
        self.editor_faces = create_empty_editor_faces()
        self.default_editor_faces = create_empty_editor_faces()
        self.last_scan_session_dir: Path | None = None
        self.last_scan_settings = {"camera": "0", "grid_size": "", "patch_size": "6"}
        self.latest_result: dict | None = None

        self.container = ttk.Frame(self.root, padding=10)
        self.container.pack(fill="both", expand=True)

        self.home_frame = ttk.Frame(self.container)
        self.scan_setup_frame = ttk.Frame(self.container)
        self.editor_frame = ttk.Frame(self.container)
        self.result_frame = ttk.Frame(self.container)

        self.scan_camera_var = StringVar(value=self.last_scan_settings["camera"])
        self.scan_grid_var = StringVar(value=self.last_scan_settings["grid_size"])
        self.scan_patch_var = StringVar(value=self.last_scan_settings["patch_size"])

        self.cell_buttons: dict[tuple[str, int], tk.Button] = {}
        self.count_labels: dict[str, ttk.Label] = {}
        self.palette_buttons: dict[str, tk.Button] = {}
        self.active_cell_popup: tk.Toplevel | None = None

        self.result_heading_var = StringVar()
        self.result_message_var = StringVar()
        self.result_solution_var = StringVar()
        self.motor_port_var = StringVar(value="")
        self.motor_status_var = StringVar(value="Motor status: not connected.")

        self._build_home_screen()
        self._build_scan_setup_screen()
        self._build_editor_screen()
        self._build_result_screen()
        self.show_home()

    def hide_all_frames(self) -> None:
        for frame in (
            self.home_frame,
            self.scan_setup_frame,
            self.editor_frame,
            self.result_frame,
        ):
            frame.pack_forget()

    def show_home(self) -> None:
        self.hide_all_frames()
        self.root.unbind("<Key>")
        self.root.unbind("<Control-Return>")
        self.root.unbind("<Control-KP_Enter>")
        self.close_cell_popup()
        self.status_var.set("Choose Manual or Camera Scan.")
        self.home_frame.pack(fill="both", expand=True)

    def start_manual_mode(self) -> None:
        self.current_mode = "manual"
        self.default_editor_faces = create_empty_editor_faces()
        self.editor_faces = clone_faces(self.default_editor_faces)
        self.editor_note_var.set("Centers are virtual and fixed.")
        self.show_editor()

    def show_scan_setup(self) -> None:
        self.hide_all_frames()
        self.root.unbind("<Key>")
        self.root.unbind("<Control-Return>")
        self.root.unbind("<Control-KP_Enter>")
        self.close_cell_popup()
        self.scan_setup_frame.pack(fill="both", expand=True)

    def show_editor(self) -> None:
        self.hide_all_frames()
        self.refresh_editor()
        self.editor_frame.pack(fill="both", expand=True)
        self.root.bind("<Key>", self.handle_editor_shortcut)
        self.root.bind("<Control-Return>", self.handle_editor_solve_shortcut)
        self.root.bind("<Control-KP_Enter>", self.handle_editor_solve_shortcut)
        self.editor_rescan_button.pack_forget()
        if self.current_mode == "camera":
            self.editor_rescan_button.pack(side="left", padx=8, before=self.editor_solve_button)
        self.root.focus_force()

    def show_result(self, result: dict) -> None:
        self.hide_all_frames()
        self.root.unbind("<Key>")
        self.root.unbind("<Control-Return>")
        self.root.unbind("<Control-KP_Enter>")
        self.close_cell_popup()
        self.latest_result = result
        self.result_heading_var.set("Solve Success" if result["success"] else "Solve Error")
        self.result_message_var.set(
            "Solution is ready." if result["success"] else (result["error"] or "Unknown error.")
        )
        self.result_solution_var.set(
            result["solution"] or ("Cube already solved." if result["success"] else "")
        )

        self._populate_result_rows(result["rows"])

        if result["success"]:
            command_lines = (
                "\n".join(f"{item['color']}, {item['angle']}" for item in result["commands"])
                if result["commands"]
                else "No robot moves needed."
            )
            summary_lines = [
                "Color counts:",
                *[f"{color}: {count}" for color, count in result["color_counts"].items()],
                "",
                f"Move count: {result['move_count']}",
            ]
        else:
            command_lines = result["error"] or ""
            summary_lines = [
                "Color counts:",
                *[f"{color}: {count}" for color, count in result["color_counts"].items()],
            ]
            if result["unknown_positions"]:
                summary_lines.extend(["", "Unknowns:", ", ".join(result["unknown_positions"])])

        self._set_text(self.result_commands_text, command_lines)
        self._set_text(self.result_summary_text, "\n".join(summary_lines))
        self.refresh_motor_ports()
        self.update_motor_section_state(result["success"])
        self.result_frame.pack(fill="both", expand=True)

    def _build_home_screen(self) -> None:
        ttk.Label(self.home_frame, text=APP_TITLE, font=("Segoe UI", 24, "bold")).pack(
            pady=(40, 10)
        )
        ttk.Label(
            self.home_frame,
            text="Choose a workflow to enter cube colors and solve.",
            font=("Segoe UI", 12),
        ).pack(pady=(0, 20))

        button_frame = ttk.Frame(self.home_frame)
        button_frame.pack(pady=18)
        ttk.Button(button_frame, text="Manual", command=self.start_manual_mode).grid(
            row=0, column=0, padx=14, ipadx=32, ipady=24
        )
        ttk.Button(button_frame, text="Camera Scan", command=self.show_scan_setup).grid(
            row=0, column=1, padx=14, ipadx=32, ipady=24
        )

        ttk.Label(self.home_frame, textvariable=self.status_var).pack(pady=(18, 8))
        ttk.Button(self.home_frame, text="Quit", command=self.root.destroy).pack()

    def _build_scan_setup_screen(self) -> None:
        ttk.Label(
            self.scan_setup_frame,
            text="Camera Scan Setup",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(18, 16))

        form = ttk.Frame(self.scan_setup_frame)
        form.pack(pady=8)
        ttk.Label(form, text="Camera index").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(form, textvariable=self.scan_camera_var, width=12).grid(
            row=0, column=1, padx=6, pady=6
        )
        ttk.Label(form, text="Grid size").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(form, textvariable=self.scan_grid_var, width=12).grid(
            row=1, column=1, padx=6, pady=6
        )
        ttk.Label(form, text="Patch size").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(form, textvariable=self.scan_patch_var, width=12).grid(
            row=2, column=1, padx=6, pady=6
        )

        ttk.Label(
            self.scan_setup_frame,
            text="Scanner opens in its own window. After all faces are scanned, this app loads the results into the review editor.",
            wraplength=720,
            justify="left",
        ).pack(pady=(10, 12))

        actions = ttk.Frame(self.scan_setup_frame)
        actions.pack(pady=14)
        ttk.Button(actions, text="Back", command=self.show_home).grid(row=0, column=0, padx=8)
        ttk.Button(actions, text="Start Scan", command=self.start_camera_scan).grid(
            row=0, column=1, padx=8
        )

    def _build_editor_screen(self) -> None:
        top = ttk.Frame(self.editor_frame)
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text="Face Editor / Review", font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(top, textvariable=self.editor_note_var, wraplength=420).pack(side="right")

        main = ttk.Frame(self.editor_frame)
        main.pack(fill="both", expand=True)

        left_panel = ttk.Frame(main, padding=(0, 0, 8, 0))
        left_panel.pack(side="left", fill="y")

        ttk.Label(left_panel, text="Palette", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(left_panel, text="Selected color:").pack(anchor="w", pady=(8, 2))
        self.selected_color_label = ttk.Label(left_panel, text="", font=("Segoe UI", 11, "bold"))
        self.selected_color_label.pack(anchor="w")

        palette = ttk.Frame(left_panel)
        palette.pack(anchor="w", pady=(8, 12))
        for index, color in enumerate(PALETTE_COLORS):
            button = tk.Button(
                palette,
                text=f"{DISPLAY_LETTERS[color]}  {color.title()}",
                command=lambda selected=color: self.set_selected_color(selected),
                width=14,
                bg=DISPLAY_COLORS[color],
                fg=TEXT_COLORS[color],
                activebackground=DISPLAY_COLORS[color],
                activeforeground=TEXT_COLORS[color],
                relief="raised",
                font=("Segoe UI", 10, "bold"),
                highlightthickness=2,
            )
            button.grid(row=index, column=0, sticky="ew", pady=2)
            self.palette_buttons[color] = button

        ttk.Label(left_panel, text="Shortcuts", font=("Segoe UI", 11, "bold")).pack(
            anchor="w", pady=(4, 4)
        )
        for color in PALETTE_COLORS:
            ttk.Label(left_panel, text=SHORTCUT_LABELS[color]).pack(anchor="w")

        ttk.Label(left_panel, text="Live counts", font=("Segoe UI", 12, "bold")).pack(
            anchor="w", pady=(12, 0)
        )
        counts_frame = ttk.Frame(left_panel)
        counts_frame.pack(anchor="w", pady=(8, 10))
        for row, color in enumerate(PALETTE_COLORS):
            ttk.Label(counts_frame, text=f"{color.title()}:").grid(
                row=row, column=0, sticky="w", padx=(0, 6), pady=1
            )
            label = ttk.Label(counts_frame, text="0")
            label.grid(row=row, column=1, sticky="w", pady=1)
            self.count_labels[color] = label

        right_panel = ttk.Frame(main)
        right_panel.pack(side="left", fill="both", expand=True)

        self.editor_scroll = ScrollableFrame(right_panel, horizontal=True)
        self.editor_scroll.pack(fill="both", expand=True)

        positions = {
            "U": (0, 1),
            "L": (1, 0),
            "F": (1, 1),
            "R": (1, 2),
            "B": (1, 3),
            "D": (2, 1),
        }
        for face, (row, column) in positions.items():
            self._build_face_widget(self.editor_scroll.content, face).grid(
                row=row, column=column, padx=10, pady=10, sticky="n"
            )

        action_bar = ttk.Frame(self.editor_frame, padding=(0, 8, 0, 0))
        action_bar.pack(fill="x", side="bottom")
        self.editor_back_button = ttk.Button(action_bar, text="Back", command=self.handle_editor_back)
        self.editor_back_button.pack(side="left", padx=(0, 8))
        self.editor_reset_button = ttk.Button(action_bar, text="Reset", command=self.reset_editor)
        self.editor_reset_button.pack(side="left", padx=8)
        self.editor_clear_button = ttk.Button(
            action_bar,
            text="Clear Outer Stickers",
            command=self.clear_outer_stickers,
        )
        self.editor_clear_button.pack(side="left", padx=8)
        self.editor_rescan_button = ttk.Button(
            action_bar,
            text="Rescan",
            command=self.rescan_current_session,
        )
        self.editor_rescan_button.pack(side="left", padx=8)
        self.editor_solve_button = tk.Button(
            action_bar,
            text="Solve",
            command=self.solve_current_faces,
            bg="#2d7d46",
            fg="#ffffff",
            activebackground="#276b3c",
            activeforeground="#ffffff",
            font=("Segoe UI", 12, "bold"),
            padx=28,
            pady=10,
            relief="raised",
            bd=3,
        )
        self.editor_solve_button.pack(side="right", padx=(8, 0))

    def _build_face_widget(self, parent: ttk.Frame, face: str) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=4, relief="ridge")
        ttk.Label(frame, text=f"{face} face", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 4)
        )

        for index in range(9):
            row = 1 + index // 3
            column = index % 3
            button = tk.Button(
                frame,
                text="",
                width=3,
                height=1,
                command=lambda selected_face=face, selected_index=index: self.handle_cell_left_click(
                    selected_face, selected_index
                ),
                font=("Segoe UI", 12, "bold"),
                relief="raised",
                bd=2,
            )
            button.grid(row=row, column=column, padx=2, pady=2, ipadx=10, ipady=8)
            button.bind(
                "<Button-3>",
                lambda _event, selected_face=face, selected_index=index: self.assign_selected_color_to_cell(
                    selected_face, selected_index
                ),
            )
            self.cell_buttons[(face, index)] = button
        return frame

    def _build_result_screen(self) -> None:
        top = ttk.Frame(self.result_frame)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, textvariable=self.result_heading_var, font=("Segoe UI", 18, "bold")).pack(
            side="left"
        )

        ttk.Label(
            self.result_frame,
            textvariable=self.result_message_var,
            wraplength=860,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        scroller = ScrollableFrame(self.result_frame, horizontal=False)
        scroller.pack(fill="both", expand=True)
        content = scroller.content

        ttk.Label(content, text="Final face rows", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.result_rows_text = tk.Text(content, height=12, width=32, wrap="none")
        self.result_rows_text.pack(fill="x", pady=(6, 10))

        ttk.Label(content, text="Solution", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        solution_frame = ttk.Frame(content)
        solution_frame.pack(fill="x", pady=(6, 10))
        ttk.Label(
            solution_frame,
            textvariable=self.result_solution_var,
            wraplength=840,
            justify="left",
        ).pack(side="left", fill="x", expand=True)
        ttk.Button(
            solution_frame,
            text="Copy Solution",
            command=lambda: self.copy_text(self.result_solution_var.get()),
        ).pack(side="right", padx=(8, 0))

        ttk.Label(content, text="Commands / Details", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        commands_frame = ttk.Frame(content)
        commands_frame.pack(fill="both", expand=True, pady=(6, 10))
        self.result_commands_text = tk.Text(commands_frame, height=14, wrap="word")
        commands_scroll = ttk.Scrollbar(
            commands_frame, orient="vertical", command=self.result_commands_text.yview
        )
        self.result_commands_text.configure(yscrollcommand=commands_scroll.set)
        self.result_commands_text.pack(side="left", fill="both", expand=True)
        commands_scroll.pack(side="right", fill="y")
        ttk.Button(
            content,
            text="Copy Commands",
            command=lambda: self.copy_text(self.result_commands_text.get("1.0", "end-1c")),
        ).pack(anchor="w", pady=(0, 12))

        ttk.Label(content, text="Diagnostics", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.result_summary_text = tk.Text(content, height=10, wrap="word")
        self.result_summary_text.pack(fill="both", expand=True, pady=(6, 10))

        ttk.Label(content, text="Motor / Arduino", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        motor_frame = ttk.Frame(content)
        motor_frame.pack(fill="x", pady=(6, 10))
        ttk.Label(motor_frame, text="COM port").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        self.motor_port_entry = ttk.Combobox(motor_frame, textvariable=self.motor_port_var, width=18)
        self.motor_port_entry.grid(row=0, column=1, sticky="w", padx=(0, 8), pady=4)
        self.motor_refresh_button = ttk.Button(motor_frame, text="Refresh Ports", command=self.refresh_motor_ports)
        self.motor_refresh_button.grid(row=0, column=2, sticky="w", padx=4, pady=4)
        self.motor_ping_button = ttk.Button(motor_frame, text="Ping Arduino", command=self.ping_motor_port)
        self.motor_ping_button.grid(row=0, column=3, sticky="w", padx=4, pady=4)
        self.motor_send_button = ttk.Button(motor_frame, text="Send All Commands", command=self.send_motor_commands)
        self.motor_send_button.grid(row=0, column=4, sticky="w", padx=4, pady=4)
        ttk.Label(motor_frame, textvariable=self.motor_status_var, wraplength=860, justify="left").grid(
            row=1, column=0, columnspan=5, sticky="w", pady=(4, 0)
        )

        action_bar = ttk.Frame(self.result_frame)
        action_bar.pack(fill="x", pady=(8, 0))
        ttk.Button(action_bar, text="Back to Editor", command=self.show_editor).pack(
            side="left", padx=6
        )
        ttk.Button(action_bar, text="Back to Home", command=self.show_home).pack(
            side="left", padx=6
        )

    def _populate_result_rows(self, rows: dict[str, list[str]]) -> None:
        lines = []
        for face, face_rows_value in rows.items():
            lines.append(f"{face}:")
            lines.extend(face_rows_value)
            lines.append("")
        self._set_text(self.result_rows_text, "\n".join(lines).strip())

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def copy_text(self, value: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.root.update()

    def refresh_motor_ports(self) -> None:
        try:
            ports = list_serial_ports()
        except MotorSerialError as exc:
            self.motor_status_var.set(f"Motor status: {exc}")
            self.motor_port_entry["values"] = ()
            return

        self.motor_port_entry["values"] = ports
        if ports and not self.motor_port_var.get():
            self.motor_port_var.set(ports[0])
        self.motor_status_var.set("Motor status: ports refreshed." if ports else "Motor status: no COM ports found.")

    def update_motor_section_state(self, solve_success: bool) -> None:
        state = "normal" if solve_success else "disabled"
        self.motor_ping_button.config(state=state)
        self.motor_send_button.config(state=state)
        self.motor_port_entry.config(state="readonly" if solve_success else "disabled")
        self.motor_refresh_button.config(state="normal")
        if not solve_success:
            self.motor_status_var.set("Motor status: solve must succeed before sending commands.")

    def ping_motor_port(self) -> None:
        port = self.motor_port_var.get().strip()
        if not port:
            self.motor_status_var.set("Motor status: choose a COM port first.")
            return
        try:
            response = ping_arduino_port(port)
        except MotorSerialError as exc:
            self.motor_status_var.set(f"Motor status: {exc}")
            messagebox.showerror("Motor / Arduino", str(exc))
            return
        self.motor_status_var.set(f"Motor status: {response} on {port}.")

    def send_motor_commands(self) -> None:
        port = self.motor_port_var.get().strip()
        if not port:
            self.motor_status_var.set("Motor status: choose a COM port first.")
            return
        if not self.latest_result or not self.latest_result.get("success"):
            self.motor_status_var.set("Motor status: no successful solution available.")
            return
        commands = [(item["color"], item["angle"]) for item in self.latest_result.get("commands", [])]
        if not commands:
            self.motor_status_var.set("Motor status: no commands to send.")
            return
        try:
            send_commands_on_port(port, commands)
        except MotorSerialError as exc:
            self.motor_status_var.set(f"Motor status: {exc}")
            messagebox.showerror("Motor / Arduino", str(exc))
            return
        self.motor_status_var.set(f"Motor status: sent {len(commands)} commands to {port}.")

    def set_selected_color(self, color: str) -> None:
        self.selected_color.set(color)
        self.update_palette_selection()

    def update_palette_selection(self) -> None:
        selected = self.selected_color.get()
        self.selected_color_label.config(
            text=f"Selected: {selected.title()} ({SHORTCUT_LABELS[selected].split()[0]})"
        )
        for color, button in self.palette_buttons.items():
            button.configure(
                relief="sunken" if color == selected else "raised",
                bd=4 if color == selected else 2,
                highlightbackground="#111111" if color == selected else DISPLAY_COLORS[color],
                highlightcolor="#111111" if color == selected else DISPLAY_COLORS[color],
            )

    def handle_cell_left_click(self, face: str, index: int) -> None:
        if index not in EDITABLE_INDEXES:
            return
        self.show_cell_popup(face, index, self.cell_buttons[(face, index)])

    def assign_selected_color_to_cell(self, face: str, index: int) -> None:
        if index not in EDITABLE_INDEXES:
            return
        self.editor_faces[face][index] = self.selected_color.get()
        self.close_cell_popup()
        self.refresh_editor()
        self.root.focus_force()

    def assign_popup_color_to_cell(self, face: str, index: int, color: str) -> None:
        self.editor_faces[face][index] = color
        self.selected_color.set(color)
        self.close_cell_popup()
        self.refresh_editor()
        self.root.focus_force()

    def show_cell_popup(self, face: str, index: int, anchor_widget: tk.Widget) -> None:
        self.close_cell_popup()
        popup = tk.Toplevel(self.root)
        popup.wm_overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#d9d9d9", padx=4, pady=4)

        x = anchor_widget.winfo_rootx() + anchor_widget.winfo_width() + 6
        y = anchor_widget.winfo_rooty()
        popup.geometry(f"+{x}+{y}")
        for option_index, color in enumerate(get_popup_color_options()):
            tk.Button(
                popup,
                text=DISPLAY_LETTERS[color],
                width=4,
                bg=DISPLAY_COLORS[color],
                fg=TEXT_COLORS[color],
                activebackground=DISPLAY_COLORS[color],
                activeforeground=TEXT_COLORS[color],
                font=("Segoe UI", 10, "bold"),
                command=lambda chosen=color: self.assign_popup_color_to_cell(face, index, chosen),
            ).grid(row=option_index // 3, column=option_index % 3, padx=2, pady=2)

        popup.bind("<FocusOut>", lambda _event: self.close_cell_popup())
        popup.focus_force()
        self.active_cell_popup = popup

    def close_cell_popup(self) -> None:
        if self.active_cell_popup is not None and self.active_cell_popup.winfo_exists():
            self.active_cell_popup.destroy()
        self.active_cell_popup = None

    def handle_editor_shortcut(self, event: tk.Event) -> None:
        if self.current_mode not in {"manual", "camera"}:
            return
        if self.editor_frame.winfo_manager() == "":
            return
        color = resolve_color_shortcut(event.keysym)
        if color is None and event.char:
            color = resolve_color_shortcut(event.char)
        if color is None:
            return
        self.set_selected_color(color)
        self.root.focus_force()

    def handle_editor_solve_shortcut(self, _event: tk.Event) -> str:
        if self.editor_frame.winfo_manager() != "":
            self.solve_current_faces()
        return "break"

    def refresh_editor(self) -> None:
        faces = inject_virtual_centers(self.editor_faces)
        for (face, index), button in self.cell_buttons.items():
            color = faces[face][index]
            center = index == 4
            button.configure(
                text=DISPLAY_LETTERS[color],
                bg=DISPLAY_COLORS[color],
                fg=TEXT_COLORS[color],
                activebackground=DISPLAY_COLORS[color],
                activeforeground=TEXT_COLORS[color],
                disabledforeground=TEXT_COLORS[color],
                relief="sunken" if center else "raised",
                bd=3 if center else 2,
                cursor="arrow" if center else "hand2",
            )
            if center:
                button.configure(command=lambda: None)
            else:
                button.configure(
                    command=lambda selected_face=face, selected_index=index: self.handle_cell_left_click(
                        selected_face, selected_index
                    )
                )

        counts = count_editor_colors(faces)
        for color, label in self.count_labels.items():
            label.config(text=str(counts[color]))
        self.update_palette_selection()

    def clear_outer_stickers(self) -> None:
        self.close_cell_popup()
        for colors in self.editor_faces.values():
            for index in EDITABLE_INDEXES:
                colors[index] = "unknown"
        self.refresh_editor()

    def reset_editor(self) -> None:
        self.close_cell_popup()
        self.editor_faces = clone_faces(self.default_editor_faces)
        self.refresh_editor()

    def handle_editor_back(self) -> None:
        self.close_cell_popup()
        self.root.unbind("<Key>")
        self.root.unbind("<Control-Return>")
        self.root.unbind("<Control-KP_Enter>")
        if self.current_mode == "camera":
            self.show_scan_setup()
        else:
            self.show_home()

    def rescan_current_session(self) -> None:
        if self.current_mode != "camera":
            self.clear_outer_stickers()
            return
        self.start_camera_scan()

    def solve_current_faces(self) -> None:
        self.close_cell_popup()
        result = solve_editor_faces(self.editor_faces)
        self.show_result(result)

    def start_camera_scan(self) -> None:
        try:
            camera_index = int(self.scan_camera_var.get().strip() or "0")
        except ValueError:
            messagebox.showerror("Camera Scan", "Camera index must be an integer.")
            return

        try:
            patch_size = int(self.scan_patch_var.get().strip() or "6")
            if patch_size <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Camera Scan", "Patch size must be a positive integer.")
            return

        grid_text = self.scan_grid_var.get().strip()
        try:
            grid_size = int(grid_text) if grid_text else None
            if grid_size is not None and grid_size <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Camera Scan", "Grid size must be a positive integer if provided."
            )
            return

        session_dir = Path("captures") / f"gui_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_dir.mkdir(parents=True, exist_ok=True)
        log_path = build_scanner_log_path(session_dir)
        command = [
            sys.executable,
            "-m",
            "rubiks_solver.live_face_scanner",
            "--camera",
            str(camera_index),
            "--scan-session",
            "--patch-size",
            str(patch_size),
            "--output-dir",
            str(session_dir),
            "--force",
        ]
        if grid_size is not None:
            command.extend(["--grid-size", str(grid_size)])

        self.last_scan_settings = {
            "camera": str(camera_index),
            "grid_size": grid_text,
            "patch_size": str(patch_size),
        }

        self.root.withdraw()
        try:
            with log_path.open("w", encoding="utf-8") as log_file:
                completed = subprocess.run(
                    command,
                    check=False,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                )
        finally:
            self.root.deiconify()
            self.root.lift()

        if completed.returncode != 0:
            messagebox.showerror(
                "Camera Scan",
                f"Camera scan did not complete successfully. Check scanner log: {log_path}",
            )
            return

        summary_path = session_dir / "session_summary.json"
        if not summary_path.exists():
            messagebox.showerror(
                "Camera Scan", "Scan session finished without a session_summary.json file."
            )
            return

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not summary.get("completed"):
            messagebox.showwarning(
                "Camera Scan",
                f"Scan session ended before all faces were saved. Check scanner log: {log_path}",
            )
            return

        try:
            loaded_faces = load_editor_faces_from_session(session_dir)
        except Exception as exc:
            messagebox.showerror("Camera Scan", f"Could not load scan session: {exc}")
            return

        self.current_mode = "camera"
        self.last_scan_session_dir = session_dir
        self.default_editor_faces = clone_faces(loaded_faces)
        self.editor_faces = clone_faces(loaded_faces)
        self.editor_note_var.set(
            f"Centers are virtual and fixed. Loaded from scan session: {session_dir.name}"
        )
        self.show_editor()


def launch_app() -> int:
    root = Tk()
    RubiksGuiApp(root)
    root.mainloop()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return launch_app()


if __name__ == "__main__":
    raise SystemExit(main())
