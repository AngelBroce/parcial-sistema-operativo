import tkinter as tk
from tkinter import ttk
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ===============================
# Modelo de Proceso y Planificador
# ===============================

ESTADOS = (
    "Nuevo",
    "Listo",
    "Ejecución",
    "Zombi",
    "Finalizado",
)

ESTADO_COLOR = {
    "Nuevo": "#D0E1FF",        # azul claro
    "Listo": "#E7FFD0",        # verde claro
    "Ejecución": "#FFF3B0",    # amarillo claro
    "Zombi": "#D6C6F5",        # lila
    "Finalizado": "#E0E0E0",    # gris
}

_id_counter = 1000

def next_pid() -> int:
    global _id_counter
    _id_counter += 1
    return _id_counter

@dataclass
class Proceso:
    pid: int
    nombre: str
    estado: str = "Nuevo"
    tiempo_llegada: float = field(default_factory=time.time)
    # Simulación automática
    tiempo_estado: int = 0           # ticks acumulados en el estado actual
    duracion_ejecucion: int = 0      # ticks que requiere en Ejecución
    linger_zombi: int = 0            # ticks que permanecerá en Zombi
    padre: Optional[int] = None
    automatizado: bool = False

    def to_row(self) -> List[str]:
        return [
            str(self.pid),
            self.nombre,
            self.estado,
            str(self.tiempo_estado),
            "Sí" if self.automatizado else "No",
        ]

class Planificador:
    def __init__(self):
        self.cola_listos: List[int] = []  # pids
        self.en_ejecucion: Optional[int] = None

    def admitir(self, proceso: Proceso):
        if proceso.estado == "Nuevo":
            proceso.estado = "Listo"
            proceso.tiempo_estado = 0
            self.cola_listos.append(proceso.pid)

    def asignar_cpu(self, procesos: Dict[int, Proceso]):
        # Si no hay ejecución actual o se liberó, tomar el siguiente listo
        if self.en_ejecucion is None and self.cola_listos:
            pid = self.cola_listos.pop(0)
            p = procesos.get(pid)
            if p and p.estado == "Listo":
                p.estado = "Ejecución"
                p.tiempo_estado = 0
                if p.duracion_ejecucion <= 0:
                    p.duracion_ejecucion = random.randint(3, 6)
                self.en_ejecucion = pid

    def tick(self, procesos: Dict[int, Proceso]):
        # En el modo automático solo aseguramos que haya asignación si está libre
        if self.en_ejecucion is None:
            self.asignar_cpu(procesos)

# ===============================
# Interfaz de Usuario Tkinter
# ===============================

class TaskManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini Administrador de Tareas - SO")
        self.geometry("1000x600")
        self.minsize(900, 550)

        # Modelo
        self.procesos: Dict[int, Proceso] = {}
        self.planificador = Planificador()

        # Configuración de reloj
        self.tick_ms = 700  # ms por tick (ajustable en UI)
        self.cpu_corriendo = False

        # Flags de automatización
        self.auto_progress = tk.BooleanVar(value=True)  # activar/desactivar cambios automáticos de estado
        self.auto_zombis = tk.BooleanVar(value=True)    # zombis aleatorios desde Ejecución
        self.auto_zombi_interval = tk.BooleanVar(value=True)  # crear 1 zombi cada 3-4 procesos creados
        self.auto_recoleccion = tk.BooleanVar(value=True)     # recolectar zombis automáticamente tras linger
        self.auto_crear_min5 = tk.BooleanVar(value=True)

        # Parámetros
        self.base_ticks_var = tk.IntVar(value=4)  # duración base de cambios (admisión/ejecución/linger)
        self._creados_desde_zombi = 0
        self._proximo_intervalo_zombi = random.choice([3, 4])

        # Construcción UI
        self._build_ui()
        self._log("Aplicación iniciada.")

        # primer refresco
        self.after(200, self._refrescar_ui)

    # ---------- Construcción UI ----------
    def _build_ui(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        # Panel izquierdo - Treeview
        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        title = ttk.Label(left, text="Procesos", font=("Segoe UI", 12, "bold"))
        title.grid(row=0, column=0, sticky="w")

        columns = ("PID", "Nombre", "Estado", "Tiempo", "Auto")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=18)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor=tk.CENTER)
        self.tree.grid(row=1, column=0, sticky="nsew")

        # Colores por estado usando tags
        for estado, color in ESTADO_COLOR.items():
            self.tree.tag_configure(estado, background=color)

        vsb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns")

        # Resumen/estado
        self.lbl_stats = ttk.Label(left, text="Resumen: 0 procesos")
        self.lbl_stats.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # Panel derecho - Controles
        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        right.columnconfigure(0, weight=1)

        # Sección CPU y flujo
        grp_cpu = ttk.LabelFrame(right, text="CPU / Flujo automático")
        grp_cpu.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.btn_start = ttk.Button(grp_cpu, text="Iniciar CPU", command=self._start_cpu)
        self.btn_stop = ttk.Button(grp_cpu, text="Pausar CPU", command=self._stop_cpu)
        self.btn_start.grid(row=0, column=0, padx=4, pady=4)
        self.btn_stop.grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(grp_cpu, text="Velocidad (ms/tick)").grid(row=1, column=0, padx=4, pady=4, sticky="e")
        self.scale_vel = tk.Scale(grp_cpu, from_=200, to=1500, orient=tk.HORIZONTAL, command=self._cambiar_velocidad)
        self.scale_vel.set(self.tick_ms)
        self.scale_vel.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        ttk.Label(grp_cpu, text="Duración base (ticks)").grid(row=2, column=0, padx=4, pady=4, sticky="e")
        self.spin_base = tk.Spinbox(grp_cpu, from_=1, to=12, width=5, textvariable=self.base_ticks_var)
        self.spin_base.grid(row=2, column=1, padx=4, pady=4, sticky="w")

        ttk.Checkbutton(grp_cpu, text="Progreso automático", variable=self.auto_progress).grid(row=3, column=0, columnspan=2, padx=4, pady=4, sticky="w")

        # Sección creación
        grp_crea = ttk.LabelFrame(right, text="Procesos")
        grp_crea.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(grp_crea, text="Nombre").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self.ent_nombre = ttk.Entry(grp_crea)
        self.ent_nombre.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.ent_nombre.insert(0, "Tarea")

        self.var_auto_proc = tk.BooleanVar(value=True)
        ttk.Checkbutton(grp_crea, text="Automatizado", variable=self.var_auto_proc).grid(row=1, column=0, columnspan=2, padx=4, pady=4, sticky="w")

        btn_crear = ttk.Button(grp_crea, text="Crear Proceso", command=self._crear_proceso)
        btn_crear.grid(row=2, column=0, padx=4, pady=4)
        btn_crear5 = ttk.Button(grp_crea, text="Crear 5", command=lambda: self._crear_varios(5))
        btn_crear5.grid(row=2, column=1, padx=4, pady=4)

        ttk.Checkbutton(grp_crea, text="Mantener mínimo 5", variable=self.auto_crear_min5).grid(row=3, column=0, columnspan=2, padx=4, pady=4, sticky="w")

        # Guía rápida
        help_txt = (
            "Guía: Si el 'Progreso automático' está activo, los procesos avanzan: \n"
            "Nuevo → Listo (espera base) → Ejecución (tarda varios ticks) → Finalizado.\n"
            "Puedes crear procesos y manipularlos manualmente en 'Acciones'."
        )
        ttk.Label(grp_crea, text=help_txt, wraplength=320, foreground="#555").grid(row=4, column=0, columnspan=2, padx=4, pady=(6, 4), sticky="w")

        # Automatización
        grp_est = ttk.LabelFrame(right, text="Automatización")
        grp_est.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Checkbutton(grp_est, text="Zombis aleatorios (en ejecución)", variable=self.auto_zombis).grid(row=0, column=0, padx=4, pady=4, sticky="w")
        ttk.Checkbutton(grp_est, text="Zombi cada 3-4 creaciones", variable=self.auto_zombi_interval).grid(row=0, column=1, padx=4, pady=4, sticky="w")
        ttk.Checkbutton(grp_est, text="Auto-recolección Zombi", variable=self.auto_recoleccion).grid(row=1, column=0, padx=4, pady=4, sticky="w")

        # Acciones manuales
        grp_acc = ttk.LabelFrame(right, text="Acciones manuales")
        grp_acc.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(grp_acc, text="Admitir Seleccionados", command=self._admitir_seleccionados).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(grp_acc, text="Admitir Nuevos", command=self._admitir_todos_nuevos).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(grp_acc, text="Forzar Ejecución", command=self._forzar_ejec_sel).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(grp_acc, text="Finalizar", command=self._finalizar_sel).grid(row=0, column=3, padx=4, pady=4)
        ttk.Button(grp_acc, text="Crear Zombi", command=self._crear_zombi).grid(row=1, column=0, padx=4, pady=4)
        ttk.Button(grp_acc, text="Recolectar Zombis", command=self._recolectar_zombis).grid(row=1, column=1, padx=4, pady=4)

        # Leyenda de colores de estados
        grp_leg = ttk.LabelFrame(right, text="Leyenda de estados")
        grp_leg.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        r = 0
        c = 0
        for estado, color in ESTADO_COLOR.items():
            swatch = tk.Canvas(grp_leg, width=16, height=16, highlightthickness=1, highlightbackground="#888")
            swatch.create_rectangle(0, 0, 16, 16, fill=color, outline="")
            ttk.Label(grp_leg, text=estado).grid(row=r, column=c*2+1, padx=(4, 10), pady=4, sticky="w")
            swatch.grid(row=r, column=c*2, padx=(6, 4), pady=4, sticky="w")
            c += 1
            if c >= 3:
                c = 0
                r += 1

        # Log
        grp_log = ttk.LabelFrame(right, text="Eventos")
        grp_log.grid(row=5, column=0, sticky="nsew")
        right.rowconfigure(5, weight=1)
        self.txt_log = tk.Text(grp_log, height=8, state="disabled")
        self.txt_log.pack(fill="both", expand=True)

    # ---------- Utilidades ----------
    def _log(self, msg: str):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def _cambiar_velocidad(self, value: str):
        try:
            self.tick_ms = max(50, int(float(value)))
        except Exception:
            pass

    def _selected_pids(self) -> List[int]:
        sel = []
        for iid in self.tree.selection():
            try:
                pid = int(self.tree.set(iid, "PID"))
                sel.append(pid)
            except Exception:
                continue
        return sel

    # ---------- Acciones ----------
    def _crear_proceso(self, nombre: Optional[str] = None, automatizado: Optional[bool] = None):
        nombre = nombre or (self.ent_nombre.get() or "Tarea")
        if automatizado is None:
            automatizado = self.var_auto_proc.get()
        pid = next_pid()
        p = Proceso(
            pid=pid,
            nombre=f"{nombre}-{pid}",
            automatizado=automatizado,
        )
        self.procesos[pid] = p
        self._log(f"Creado proceso {p.nombre} (PID={pid}). Estado: Nuevo.")

        # Zombi por intervalo de creaciones
        self._creados_desde_zombi += 1
        if self.auto_zombi_interval.get() and self._creados_desde_zombi >= self._proximo_intervalo_zombi:
            p.estado = "Zombi"
            p.tiempo_estado = 0
            base = self.base_ticks_var.get()
            p.linger_zombi = random.randint(max(1, base), max(2, base + 2))
            self._log(f"Creación especial: {p.nombre} nace en estado Zombi (linger={p.linger_zombi}).")
            self._creados_desde_zombi = 0
            self._proximo_intervalo_zombi = random.choice([3, 4])

        self._refrescar_tree()

    def _crear_varios(self, n: int):
        for _ in range(n):
            self._crear_proceso()

    def _admitir_seleccionados(self):
        for pid in self._selected_pids():
            p = self.procesos.get(pid)
            if p and p.estado == "Nuevo":
                self.planificador.admitir(p)
                self._log(f"Admitido manualmente a Listo: PID {pid}.")
        self._refrescar_tree()

    def _admitir_todos_nuevos(self):
        for p in self.procesos.values():
            if p.estado == "Nuevo":
                self.planificador.admitir(p)
        self._log("Todos los 'Nuevo' admitidos a Listo.")
        self._refrescar_tree()

    def _forzar_ejec_sel(self):
        sel = self._selected_pids()
        if not sel:
            return
        pid = sel[0]
        p = self.procesos.get(pid)
        if not p:
            return
        # Preempt actual
        if self.planificador.en_ejecucion is not None and self.planificador.en_ejecucion != pid:
            actual = self.procesos.get(self.planificador.en_ejecucion)
            if actual and actual.estado == "Ejecución":
                actual.estado = "Listo"
                actual.tiempo_estado = 0
                self.planificador.cola_listos.insert(0, actual.pid)
        # Quitar de cola listos si está
        if p.pid in self.planificador.cola_listos:
            self.planificador.cola_listos.remove(p.pid)
        # Subir a ejecución
        if p.estado == "Nuevo":
            self.planificador.admitir(p)
        p.estado = "Ejecución"
        p.tiempo_estado = 0
        base = self.base_ticks_var.get()
        if p.duracion_ejecucion <= 0:
            p.duracion_ejecucion = random.randint(max(1, base), max(2, base + 2))
        self.planificador.en_ejecucion = p.pid
        self._log(f"Forzado a Ejecución: PID {p.pid}.")
        self._refrescar_tree()

    def _finalizar_sel(self):
        for pid in self._selected_pids():
            p = self.procesos.get(pid)
            if not p:
                continue
            if self.planificador.en_ejecucion == pid:
                self.planificador.en_ejecucion = None
            p.estado = "Finalizado"
            p.tiempo_estado = 0
            self._log(f"Finalizado manualmente PID {pid}.")
        self._refrescar_tree()

    def _crear_zombi(self):
        for pid in self._selected_pids():
            p = self.procesos.get(pid)
            if not p:
                continue
            if self.planificador.en_ejecucion == pid:
                self.planificador.en_ejecucion = None
            p.estado = "Zombi"
            p.tiempo_estado = 0
            base = self.base_ticks_var.get()
            p.linger_zombi = random.randint(max(1, base), max(2, base + 3))
            self._log(f"PID {pid} enviado a Zombi (linger={p.linger_zombi}).")
        self._refrescar_tree()

    def _recolectar_zombis(self):
        reco = 0
        for p in self.procesos.values():
            if p.estado == "Zombi":
                p.estado = "Finalizado"
                p.tiempo_estado = 0
                reco += 1
        if reco:
            self._log(f"Recolectados {reco} zombi(s) manualmente.")
        self._refrescar_tree()

    def _start_cpu(self):
        if not self.cpu_corriendo:
            self.cpu_corriendo = True
            self._log("CPU iniciada.")
            self._tick_loop()

    def _stop_cpu(self):
        self.cpu_corriendo = False
        self._log("CPU pausada.")

    # ---------- Bucle principal de ticks ----------
    def _tick_loop(self):
        if not self.cpu_corriendo:
            return

        # 1) Mantener mínimo 5 procesos vivos (no finalizados)
        if self.auto_crear_min5.get():
            vivos = [p for p in self.procesos.values() if p.estado != "Finalizado"]
            if len(vivos) < 5:
                for _ in range(5 - len(vivos)):
                    self._crear_proceso(automatizado=True)

        # 2) Cambios automáticos de estado
        if self.auto_progress.get():
            base = self.base_ticks_var.get()
            # Nuevo -> Listo tras base ticks
            for p in self.procesos.values():
                if p.estado == "Nuevo":
                    p.tiempo_estado += 1
                    if p.tiempo_estado >= max(1, base):
                        self.planificador.admitir(p)
                        self._log(f"Admitido automáticamente a Listo: PID {p.pid}.")

            # Asignar CPU si libre
            if self.planificador.en_ejecucion is None and self.planificador.cola_listos:
                self.planificador.asignar_cpu(self.procesos)

            # Avanzar ejecución / zombis aleatorios
            pid = self.planificador.en_ejecucion
            if pid is not None:
                p = self.procesos.get(pid)
                if p and p.estado == "Ejecución":
                    if p.duracion_ejecucion <= 0:
                        p.duracion_ejecucion = random.randint(max(1, base), max(2, base + 2))
                    p.tiempo_estado += 1
                    if self.auto_zombis.get() and p.automatizado and random.random() < 0.06:
                        p.estado = "Zombi"
                        p.tiempo_estado = 0
                        p.linger_zombi = random.randint(max(1, base), max(2, base + 2))
                        self.planificador.en_ejecucion = None
                        self._log(f"PID {p.pid} pasó a Zombi aleatoriamente.")
                    elif p.tiempo_estado >= p.duracion_ejecucion:
                        p.estado = "Finalizado"
                        self.planificador.en_ejecucion = None
                        self._log(f"PID {p.pid} finalizó su ejecución.")

        # 3) Recolección automática de zombis (independiente del progreso auto)
        if self.auto_recoleccion.get():
            base = self.base_ticks_var.get()
            for p in self.procesos.values():
                if p.estado == "Zombi":
                    p.tiempo_estado += 1
                    if p.linger_zombi <= 0:
                        p.linger_zombi = random.randint(max(1, base), max(2, base + 2))
                    if p.tiempo_estado >= p.linger_zombi:
                        p.estado = "Finalizado"
                        p.tiempo_estado = 0
                        self._log(f"PID {p.pid} recolectado de Zombi -> Finalizado.")

        # 4) Refrescar vista
        self._refrescar_tree()

        # Programar siguiente tick
        self.after(self.tick_ms, self._tick_loop)

    # ---------- Refresco de Treeview ----------
    def _refrescar_tree(self):
        # Sync items
        existentes = set(self.tree.get_children())
        por_pid = {self.tree.set(i, "PID"): i for i in existentes}

        # actualizar/insertar
        for p in self.procesos.values():
            row = p.to_row()
            pid_str = str(p.pid)
            if pid_str in por_pid:
                iid = por_pid[pid_str]
                for col, val in zip(("PID", "Nombre", "Estado", "Tiempo", "Auto"), row):
                    self.tree.set(iid, col, val)
                # actualizar tag de color según estado
                self.tree.item(iid, tags=(p.estado,))
            else:
                iid = self.tree.insert("", "end", values=row, tags=(p.estado,))
                por_pid[pid_str] = iid

        # eliminar los que ya no existen
        actuales_pids = {str(p.pid) for p in self.procesos.values()}
        for pid_str, iid in por_pid.items():
            if pid_str not in actuales_pids:
                self.tree.delete(iid)

        # actualizar resumen
        total = len(self.procesos)
        por_estado: Dict[str, int] = {e: 0 for e in ESTADOS}
        for p in self.procesos.values():
            por_estado[p.estado] = por_estado.get(p.estado, 0) + 1
        resumen = " | ".join([f"{e}: {por_estado.get(e, 0)}" for e in ESTADOS])
        self.lbl_stats.configure(text=f"Resumen: {total} proceso(s) | {resumen}")

    def _refrescar_ui(self):
        # botón start/stop
        self.btn_start.configure(state=("disabled" if self.cpu_corriendo else "normal"))
        self.btn_stop.configure(state=("normal" if self.cpu_corriendo else "disabled"))
        # refrescar árbol periódicamente
        self._refrescar_tree()
        self.after(500, self._refrescar_ui)

# ===============================
# Entrada principal
# ===============================

def main():
    app = TaskManagerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
