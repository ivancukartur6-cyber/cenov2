#!/usr/bin/env python3
"""
CenoV2 — Power Management
sudo dnf install python3-tkinter
"""

import tkinter as tk
import subprocess, threading, os, re, time, math

# ── palette ──────────────────────────────────────────────
BG     = "#0c0c12"
SURF   = "#13131e"
BORDER = "#1e1e2c"
TEXT   = "#d8dce8"
MUTED  = "#4a4f6a"
ACCENT = "#00d4ff"
GREEN  = "#00c97a"
RED    = "#ff4555"
AMBER  = "#ffb340"

COLS = {"performance": RED, "balanced": ACCENT, "power-saver": GREEN}
FM = lambda s, bold=False: ("Courier New", s, "bold" if bold else "normal")
FH = lambda s, bold=False: ("Helvetica",   s, "bold" if bold else "normal")


# ── backend ──────────────────────────────────────────────
class Backend:
    @staticmethod
    def method():
        for exe, key in [("powerprofilesctl", "ppd"), ("cpupower", "cpu")]:
            if subprocess.run(["which", exe], capture_output=True).returncode == 0:
                return key
        if os.path.exists("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"):
            return "sys"
        return None

    @staticmethod
    def current():
        try:
            r = subprocess.run(["powerprofilesctl", "get"],
                               capture_output=True, text=True, timeout=3)
            if r.returncode == 0:
                raw = r.stdout.strip()
                return "power-saver" if "saver" in raw else raw
        except Exception:
            pass
        try:
            g = open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor").read().strip()
            return {"powersave": "power-saver", "schedutil": "balanced",
                    "performance": "performance"}.get(g, "balanced")
        except Exception:
            return None

    @staticmethod
    def apply(mode, meth):
        GOV = {"performance": "performance", "balanced": "schedutil", "power-saver": "powersave"}
        if meth == "ppd":
            cmd = ["powerprofilesctl", "set", mode]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                ok = r.returncode == 0
                return ok, [f"$ powerprofilesctl set {mode}",
                            f"[{'OK' if ok else 'ERR'}] {r.stderr.strip() or mode}"]
            except Exception as e:
                return False, [f"$ powerprofilesctl set {mode}", f"[ERR] {e}"]

        if meth == "cpu":
            gov = GOV[mode]
            cmd = ["sudo", "cpupower", "frequency-set", "-g", gov]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                ok = r.returncode == 0
                return ok, [f"$ sudo cpupower frequency-set -g {gov}",
                            f"[{'OK' if ok else 'ERR'}] {(r.stderr or r.stdout).strip() or gov}"]
            except Exception as e:
                return False, [f"$ sudo cpupower frequency-set -g {gov}", f"[ERR] {e}"]

        if meth == "sys":
            gov = GOV[mode]
            n, err = 0, None
            for cpu in os.listdir("/sys/devices/system/cpu/"):
                p = f"/sys/devices/system/cpu/{cpu}/cpufreq/scaling_governor"
                if os.path.exists(p):
                    try:
                        open(p, "w").write(gov); n += 1
                    except Exception as e:
                        err = str(e)
            if err and n == 0:
                return False, [f"$ echo {gov} > .../scaling_governor",
                               f"[ERR] {err}", "Hint: run with sudo"]
            return True, [f"$ echo {gov} > .../scaling_governor",
                          f"[OK] governor '{gov}' on {n} cpu(s)"]

        return False, ["[ERR] no power method found"]

    @staticmethod
    def governor():
        try:
            return open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor").read().strip()
        except Exception:
            return None

    @staticmethod
    def battery():
        for p in ["/sys/class/power_supply/BAT0", "/sys/class/power_supply/BAT1"]:
            if os.path.exists(p):
                try:
                    cap = open(f"{p}/capacity").read().strip()
                    st  = open(f"{p}/status").read().strip()
                    return int(cap), st
                except Exception:
                    pass
        return None, None

    @staticmethod
    def on_ac():
        for n in ["AC", "AC0", "ADP0", "ADP1"]:
            p = f"/sys/class/power_supply/{n}/online"
            if os.path.exists(p):
                try:
                    return open(p).read().strip() == "1"
                except Exception:
                    pass
        return None


# ── animated logo ─────────────────────────────────────────
class Logo(tk.Canvas):
    def __init__(self, parent, sz=36, bg=BG, **kw):
        super().__init__(parent, width=sz, height=sz, bg=bg,
                         highlightthickness=0, **kw)
        self.sz, self.t = sz, 0
        self._tick()

    def _tick(self):
        self.delete("all")
        cx = cy = self.sz / 2
        r1 = cx * 0.85
        r2 = cx * 0.55
        ri = cx * 0.18

        for i in range(8):
            a = math.radians(self.t * 0.5 + i * 45)
            col = ACCENT if i % 2 == 0 else MUTED
            lw  = 1.5 if i % 2 == 0 else 1
            self.create_line(
                cx + r2 * math.cos(a), cy + r2 * math.sin(a),
                cx + r1 * math.cos(a), cy + r1 * math.sin(a),
                fill=col, width=lw)

        for i in range(3):
            a = math.radians(-self.t * 0.8 + i * 120)
            self.create_line(
                cx + ri * math.cos(a), cy + ri * math.sin(a),
                cx + r2 * 0.75 * math.cos(a), cy + r2 * 0.75 * math.sin(a),
                fill="#7c3aed", width=1)

        p = ri * (0.6 + 0.4 * math.sin(math.radians(self.t * 4)))
        self.create_oval(cx - p, cy - p, cx + p, cy + p, fill=ACCENT, outline="")
        self.t += 2
        self.after(28, self._tick)


# ── log widget ────────────────────────────────────────────
class Log(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=SURF, **kw)
        self.txt = tk.Text(self, height=7, bg=SURF, fg=MUTED,
                           font=FM(9), bd=0, padx=10, pady=8,
                           state="disabled", wrap="word",
                           insertbackground=ACCENT,
                           selectbackground=BORDER,
                           highlightthickness=1,
                           highlightbackground=BORDER)
        self.txt.pack(fill="both", expand=True)
        self.txt.tag_config("cmd", foreground="#8b7cf8")
        self.txt.tag_config("ok",  foreground=GREEN)
        self.txt.tag_config("err", foreground=RED)
        self.txt.tag_config("inf", foreground=ACCENT)

    def write(self, msg, tag=""):
        self.txt.config(state="normal")
        self.txt.insert("end", msg + "\n", tag)
        self.txt.see("end")
        self.txt.config(state="disabled")


# ── main app ──────────────────────────────────────────────
class App(tk.Tk):
    MODES = [
        ("performance", "PERFORMANCE", "Max CPU / gaming"),
        ("balanced",    "BALANCED",    "Adaptive / daily use"),
        ("power-saver", "POWER SAVER", "Battery / quiet"),
    ]

    def __init__(self):
        super().__init__()
        self.title("CenoV2")
        self.geometry("560x520")
        self.minsize(480, 440)
        self.resizable(True, True)
        self.configure(bg=BG)

        self.be       = Backend()
        self.meth     = self.be.method()
        self.applied  = None   # confirmed active mode
        self.selected = None   # user's pending pick
        self._btns    = {}

        self._build()
        self._read_current()
        self._status_tick()

    # ── layout ───────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=18)
        hdr.pack(fill="x", padx=28)

        Logo(hdr, sz=36, bg=BG).pack(side="left", padx=(0, 12))

        tf = tk.Frame(hdr, bg=BG)
        tf.pack(side="left")
        tk.Label(tf, text="CenoV2", font=FM(14, True),
                 fg=TEXT, bg=BG).pack(anchor="w")
        tk.Label(tf, text="power management", font=FH(9),
                 fg=MUTED, bg=BG).pack(anchor="w")

        self._bat_lbl = tk.Label(hdr, text="", font=FM(9),
                                 fg=MUTED, bg=BG)
        self._bat_lbl.pack(side="right")

        tk.Frame(self, height=1, bg=BORDER).pack(fill="x")

        # Mode buttons
        mid = tk.Frame(self, bg=BG, pady=20)
        mid.pack(fill="x", padx=28)

        for mode, name, sub in self.MODES:
            btn = self._mode_btn(mid, mode, name, sub)
            btn.pack(fill="x", pady=4)
            self._btns[mode] = btn

        tk.Frame(self, height=1, bg=BORDER).pack(fill="x")

        # Bottom: apply + status
        bot = tk.Frame(self, bg=BG, pady=16)
        bot.pack(fill="x", padx=28)

        self.btn_apply = tk.Button(
            bot, text="APPLY", font=FM(10, True),
            bg=ACCENT, fg="#000", bd=0,
            padx=24, pady=9, cursor="hand2",
            activebackground="#00b5d8", activeforeground="#000",
            command=self._apply)
        self.btn_apply.pack(side="left")

        self._hint = tk.Label(bot, text="select a mode", font=FH(9),
                              fg=MUTED, bg=BG)
        self._hint.pack(side="left", padx=14)

        self._gov_lbl = tk.Label(bot, text="", font=FM(8),
                                 fg=MUTED, bg=BG)
        self._gov_lbl.pack(side="right")

        tk.Frame(self, height=1, bg=BORDER).pack(fill="x")

        # Log
        self.log = Log(self)
        self.log.pack(fill="both", expand=True, padx=0, pady=0)

        self.log.write("// CenoV2 ready", "inf")
        self.log.write(f"// method: {self.meth or 'none detected'}", "inf")

    def _mode_btn(self, parent, mode, name, sub):
        color = COLS[mode]
        outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1, cursor="hand2")

        inner = tk.Frame(outer, bg=SURF, padx=16, pady=12, cursor="hand2")
        inner.pack(fill="both", expand=True)

        # left accent stripe
        stripe = tk.Frame(inner, bg=color, width=2)
        stripe.pack(side="left", fill="y", padx=(0, 12))

        txt = tk.Frame(inner, bg=SURF)
        txt.pack(side="left", fill="x", expand=True)

        tk.Label(txt, text=name, font=FM(10, True),
                 fg=TEXT, bg=SURF).pack(anchor="w")
        tk.Label(txt, text=sub, font=FH(9),
                 fg=MUTED, bg=SURF).pack(anchor="w")

        # badge — hidden until applied
        badge = tk.Label(inner, text="active", font=FM(8),
                         fg=color, bg=SURF)

        outer._inner  = inner
        outer._badge  = badge
        outer._color  = color
        outer._stripe = stripe

        for w in [outer, inner, txt, stripe]:
            w.bind("<Button-1>", lambda e, m=mode: self._select(m))
        for child in txt.winfo_children():
            child.bind("<Button-1>", lambda e, m=mode: self._select(m))

        return outer

    # ── state ─────────────────────────────────────────────
    def _select(self, mode):
        self.selected = mode
        for m, btn in self._btns.items():
            sel = (m == mode)
            btn.config(bg=btn._color if sel else BORDER)
            btn._inner.config(bg=SURF if not sel else SURF)
        self._hint.config(text=f"{mode}  —  press apply", fg=AMBER)

    def _mark_active(self, mode):
        self.applied = mode
        for m, btn in self._btns.items():
            if m == mode:
                btn._badge.pack(side="right")
            else:
                btn._badge.pack_forget()

    def _read_current(self):
        def read():
            cur = self.be.current()
            if cur:
                self.after(0, self._mark_active, cur)
        threading.Thread(target=read, daemon=True).start()

    def _apply(self):
        if not self.selected:
            self._hint.config(text="select a mode first", fg=RED)
            return
        if not self.meth:
            self.log.write("[ERR] no power tool found — install power-profiles-daemon", "err")
            return
        if self.selected == self.applied:
            self._hint.config(text=f"already on {self.selected}", fg=MUTED)
            return

        self.btn_apply.config(state="disabled", text="...")
        mode, meth = self.selected, self.meth

        def run():
            ok, lines = self.be.apply(mode, meth)
            for line in lines:
                tag = "ok" if "[OK]" in line else "err" if "[ERR]" in line else "cmd"
                self.after(0, self.log.write, line, tag)
            self.after(0, self._done, ok, mode)

        threading.Thread(target=run, daemon=True).start()

    def _done(self, ok, mode):
        self.btn_apply.config(state="normal", text="APPLY")
        if ok:
            # clear selection highlight
            for btn in self._btns.values():
                btn.config(bg=BORDER)
            self.selected = None
            self._mark_active(mode)
            self._hint.config(text=f"applied: {mode}", fg=GREEN)
        else:
            self._hint.config(text="failed — see log", fg=RED)

    # ── status footer tick ────────────────────────────────
    def _status_tick(self):
        # governor
        gov = self.be.governor()
        self._gov_lbl.config(
            text=f"gov: {gov}" if gov else "gov: N/A",
            fg=MUTED)

        # battery
        cap, st = self.be.battery()
        if cap is not None:
            ac = self.be.on_ac()
            plug = "  AC" if ac else ""
            self._bat_lbl.config(text=f"{cap}%{plug}")
        else:
            self._bat_lbl.config(text="")

        self.after(6000, self._status_tick)


if __name__ == "__main__":
    App().mainloop()
