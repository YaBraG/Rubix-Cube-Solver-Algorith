"""Tkinter desktop app for manual and camera-assisted cube solving."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
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


APP_TITLE = "Rubik's Cube Solver App"
PALETTE_COLORS = ["white", "yellow", "green", "blue", "red", "orange", "unknown"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rubiks-gui-app",
        description="Launch the Tkinter desktop app for manual and camera-assisted solving.",
    )
    return parser


class RubiksGuiApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1200x850")
        self.root.minsize(980, 720)

        self.current_mode = "manual"
        self.selected_color = StringVar(value="white")
        self.status_var = StringVar(value="Choose Manual or Camera Scan.")
        self.editor_note_var = StringVar(value="Centers are virtual and fixed.")
        self.editor_faces = create_empty_editor_faces()
        self.default_editor_faces = create_empty_editor_faces()
        self.last_scan_session_dir: Path | None = None
        self.last_scan_settings = {"camera": "0", "grid_size": "", "patch_size": "6"}

        self.container = ttk.Frame(self.root, padding=16)
        self.container.pack(fill="both", expand=True)

        self.home_frame = ttk.Frame(self.container)
        self.scan_setup_frame = ttk.Frame(self.container)
        self.editor_frame = ttk.Frame(self.container)
        self.result_frame = ttk.Frame(self.container)

        self.scan_camera_var = StringVar(value=self.last_scan_settings["camera"])
        self.scan_grid_var = StringVar(value=self.last_scan_settings["grid_size"])
        self.scan_patch_var = StringVar(value=self.last_scan_settings["patch_size"])

        self.cell_buttons: dict[tuple[str, int], ttk.Button] = {}
        self.palette_buttons: dict[str, ttk.Button] = {}
        self.count_labels: dict[str, ttk.Label] = {}

        self.result_heading_var = StringVar()
        self.result_message_var = StringVar()
        self.result_solution_var = StringVar()
        self.result_commands_var = StringVar()

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
        self.scan_setup_frame.pack(fill="both", expand=True)

    def show_editor(self) -> None:
        self.hide_all_frames()
        self.refresh_editor()
        self.editor_frame.pack(fill="both", expand=True)

    def show_result(self, result: dict) -> None:
        self.hide_all_frames()
        if result["success"]:
            self.result_heading_var.set("Solve Success")
            solution_text = result["solution"] or "Cube already solved."
            command_lines = (
                "\n".join(f"{item['color']}, {item['angle']}" for item in result["commands"])
                if result["commands"]
                else "No robot moves needed."
            )
            self.result_message_var.set("Solution is ready.")
            self.result_solution_var.set(solution_text)
            self.result_commands_var.set(command_lines)
        else:
            self.result_heading_var.set("Solve Error")
            self.result_message_var.set(result["error"] or "Unknown error.")
            self.result_solution_var.set("")
            diagnostics = []
            diagnostics.append("Color counts:")
            for color, count in result["color_counts"].items():
                diagnostics.append(f"  {color}: {count}")
            if result["unknown_positions"]:
                diagnostics.append("Unknowns: " + ", ".join(result["unknown_positions"]))
            diagnostics.append("")
            diagnostics.append("Face rows:")
            for face, rows in result["rows"].items():
                diagnostics.append(f"{face}:")
                diagnostics.extend(rows)
            self.result_commands_var.set("\n".join(diagnostics))

        self._populate_result_rows(result["rows"])
        self.result_frame.pack(fill="both", expand=True)

    def _build_home_screen(self) -> None:
        title = ttk.Label(self.home_frame, text=APP_TITLE, font=("Segoe UI", 24, "bold"))
        title.pack(pady=(60, 12))

        subtitle = ttk.Label(
            self.home_frame,
            text="Choose a workflow to enter cube colors and solve.",
            font=("Segoe UI", 12),
        )
        subtitle.pack(pady=(0, 30))

        button_frame = ttk.Frame(self.home_frame)
        button_frame.pack(pady=20)

        manual_button = ttk.Button(button_frame, text="Manual", command=self.start_manual_mode)
        manual_button.grid(row=0, column=0, padx=18, ipadx=40, ipady=30)

        camera_button = ttk.Button(button_frame, text="Camera Scan", command=self.show_scan_setup)
        camera_button.grid(row=0, column=1, padx=18, ipadx=40, ipady=30)

        ttk.Label(self.home_frame, textvariable=self.status_var).pack(pady=(24, 8))
        ttk.Button(self.home_frame, text="Quit", command=self.root.destroy).pack(pady=(8, 0))

    def _build_scan_setup_screen(self) -> None:
        ttk.Label(
            self.scan_setup_frame,
            text="Camera Scan Setup",
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=(20, 20))

        form = ttk.Frame(self.scan_setup_frame)
        form.pack(pady=10)

        ttk.Label(form, text="Camera index").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(form, textvariable=self.scan_camera_var, width=12).grid(
            row=0, column=1, sticky="w", padx=6, pady=6
        )

        ttk.Label(form, text="Grid size").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(form, textvariable=self.scan_grid_var, width=12).grid(
            row=1, column=1, sticky="w", padx=6, pady=6
        )

        ttk.Label(form, text="Patch size").grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(form, textvariable=self.scan_patch_var, width=12).grid(
            row=2, column=1, sticky="w", padx=6, pady=6
        )

        ttk.Label(
            self.scan_setup_frame,
            text="Scanner opens in its own window. Scan all faces, then this app will load the results.",
            wraplength=700,
        ).pack(pady=(16, 10))

        actions = ttk.Frame(self.scan_setup_frame)
        actions.pack(pady=18)
        ttk.Button(actions, text="Back", command=self.show_home).grid(row=0, column=0, padx=8)
        ttk.Button(actions, text="Start Scan", command=self.start_camera_scan).grid(
            row=0, column=1, padx=8
        )

    def _build_editor_screen(self) -> None:
        top = ttk.Frame(self.editor_frame)
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text="Face Editor / Review", font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(top, textvariable=self.editor_note_var).pack(side="right")

        main = ttk.Frame(self.editor_frame)
        main.pack(fill="both", expand=True)

        left_panel = ttk.Frame(main)
        left_panel.pack(side="left", fill="y", padx=(0, 18))

        ttk.Label(left_panel, text="Palette", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(left_panel, text="Selected color:").pack(anchor="w", pady=(12, 4))
        ttk.Label(left_panel, textvariable=self.selected_color, font=("Segoe UI", 11, "bold")).pack(
            anchor="w"
        )

        palette = ttk.Frame(left_panel)
        palette.pack(anchor="w", pady=(10, 16))
        for index, color in enumerate(PALETTE_COLORS):
            button = ttk.Button(
                palette,
                text=color.title(),
                command=lambda selected=color: self.set_selected_color(selected),
                width=14,
            )
            button.grid(row=index, column=0, sticky="ew", pady=3)
            self.palette_buttons[color] = button

        ttk.Label(left_panel, text="Live counts", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        counts_frame = ttk.Frame(left_panel)
        counts_frame.pack(anchor="w", pady=(8, 12))
        for row, color in enumerate(PALETTE_COLORS):
            ttk.Label(counts_frame, text=f"{color.title()}:").grid(
                row=row, column=0, sticky="w", padx=(0, 6), pady=2
            )
            label = ttk.Label(counts_frame, text="0")
            label.grid(row=row, column=1, sticky="w", pady=2)
            self.count_labels[color] = label

        action_frame = ttk.Frame(left_panel)
        action_frame.pack(anchor="w", pady=(16, 0))
        ttk.Button(action_frame, text="Back", command=self.handle_editor_back).grid(
            row=0, column=0, padx=4, pady=4
        )
        ttk.Button(action_frame, text="Reset", command=self.reset_editor).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Button(action_frame, text="Clear Outer Stickers", command=self.clear_outer_stickers).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=4
        )
        ttk.Button(action_frame, text="Rescan", command=self.rescan_current_session).grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=4, pady=4
        )
        ttk.Button(action_frame, text="Solve", command=self.solve_current_faces).grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=8
        )

        right_panel = ttk.Frame(main)
        right_panel.pack(side="left", fill="both", expand=True)

        self.grid_container = ttk.Frame(right_panel)
        self.grid_container.pack(pady=12)

        positions = {
            "U": (0, 1),
            "L": (1, 0),
            "F": (1, 1),
            "R": (1, 2),
            "B": (1, 3),
            "D": (2, 1),
        }
        for face, (row, column) in positions.items():
            self._build_face_widget(self.grid_container, face).grid(
                row=row, column=column, padx=14, pady=14, sticky="n"
            )

    def _build_face_widget(self, parent: ttk.Frame, face: str) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=4, relief="ridge")
        ttk.Label(frame, text=f"{face} face", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(0, 6)
        )

        for index in range(9):
            row = 1 + index // 3
            column = index % 3
            button = ttk.Button(
                frame,
                text="",
                width=6,
                command=lambda selected_face=face, selected_index=index: self.assign_cell_color(
                    selected_face, selected_index
                ),
            )
            button.grid(row=row, column=column, padx=2, pady=2, ipadx=8, ipady=8)
            self.cell_buttons[(face, index)] = button
        return frame

    def _build_result_screen(self) -> None:
        top = ttk.Frame(self.result_frame)
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, textvariable=self.result_heading_var, font=("Segoe UI", 18, "bold")).pack(
            side="left"
        )

        ttk.Label(self.result_frame, textvariable=self.result_message_var, wraplength=900).pack(
            anchor="w", pady=(0, 12)
        )

        middle = ttk.Frame(self.result_frame)
        middle.pack(fill="both", expand=True)

        left = ttk.Frame(middle)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        ttk.Label(left, text="Final face rows", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.result_rows_text = ttk.Label(left, justify="left")
        self.result_rows_text.pack(anchor="w", pady=(8, 0))

        right = ttk.Frame(middle)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))
        ttk.Label(right, text="Solution", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(right, textvariable=self.result_solution_var, wraplength=400, justify="left").pack(
            anchor="w", pady=(8, 12)
        )
        ttk.Label(right, text="Commands / Details", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(right, textvariable=self.result_commands_var, wraplength=420, justify="left").pack(
            anchor="w", pady=(8, 0)
        )

        actions = ttk.Frame(self.result_frame)
        actions.pack(pady=18)
        ttk.Button(actions, text="Back to Editor", command=self.show_editor).grid(
            row=0, column=0, padx=8
        )
        ttk.Button(actions, text="Back to Home", command=self.show_home).grid(
            row=0, column=1, padx=8
        )

    def _populate_result_rows(self, rows: dict[str, list[str]]) -> None:
        lines = []
        for face, face_rows_value in rows.items():
            lines.append(f"{face}:")
            lines.extend(face_rows_value)
            lines.append("")
        self.result_rows_text.config(text="\n".join(lines).strip())

    def set_selected_color(self, color: str) -> None:
        self.selected_color.set(color)

    def assign_cell_color(self, face: str, index: int) -> None:
        if index not in EDITABLE_INDEXES:
            return
        self.editor_faces[face][index] = self.selected_color.get()
        self.refresh_editor()

    def refresh_editor(self) -> None:
        faces = inject_virtual_centers(self.editor_faces)
        for (face, index), button in self.cell_buttons.items():
            color = faces[face][index]
            button.config(
                text=DISPLAY_LETTERS[color],
                state="disabled" if index == 4 else "normal",
            )
            style_name = self._style_name_for_color(color, index == 4)
            button.config(style=style_name)

        counts = count_editor_colors(faces)
        for color, label in self.count_labels.items():
            label.config(text=str(counts[color]))

    def _style_name_for_color(self, color: str, center: bool) -> str:
        name = f"{color}.{'center' if center else 'cell'}.TButton"
        style = ttk.Style(self.root)
        style.configure(
            name,
            background=DISPLAY_COLORS[color],
            foreground=TEXT_COLORS[color],
            font=("Segoe UI", 10, "bold"),
            relief="sunken" if center else "raised",
        )
        style.map(name, background=[("active", DISPLAY_COLORS[color])])
        return name

    def clear_outer_stickers(self) -> None:
        for face, colors in self.editor_faces.items():
            for index in EDITABLE_INDEXES:
                colors[index] = "unknown"
        self.refresh_editor()

    def reset_editor(self) -> None:
        self.editor_faces = clone_faces(self.default_editor_faces)
        self.refresh_editor()

    def handle_editor_back(self) -> None:
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
            messagebox.showerror("Camera Scan", "Grid size must be a positive integer if provided.")
            return

        session_dir = Path("captures") / f"gui_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
            completed = subprocess.run(command, check=False)
        finally:
            self.root.deiconify()
            self.root.lift()

        if completed.returncode != 0:
            messagebox.showerror(
                "Camera Scan",
                "Camera scan did not complete successfully. Review the scanner window output and try again.",
            )
            return

        summary_path = session_dir / "session_summary.json"
        if not summary_path.exists():
            messagebox.showerror("Camera Scan", "Scan session finished without a session_summary.json file.")
            return

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not summary.get("completed"):
            messagebox.showwarning(
                "Camera Scan",
                "Scan session ended before all faces were saved. Complete the scan and try again.",
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
