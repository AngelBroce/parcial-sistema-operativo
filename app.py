import tkinter as tk
from tkinter import ttk
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ===============================
# Ventana de Auditoría
# ===============================

class VentanaAuditoria(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Auditoría del Sistema - Log de Eventos")
        self.geometry("600x400")
        self.minsize(500, 300)
        
        # Configurar ventana
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        
        # Área de texto para el log
        frame_log = ttk.LabelFrame(self, text="Registro de Eventos del Sistema")
        frame_log.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        frame_log.rowconfigure(0, weight=1)
        frame_log.columnconfigure(0, weight=1)
        
        self.txt_log = tk.Text(frame_log, state="disabled", wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(frame_log, orient="vertical", command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=scrollbar.set)
        
        self.txt_log.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=4)
        
        # Botón para limpiar log
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
        
        ttk.Button(btn_frame, text="Limpiar Log", command=self.limpiar_log).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cerrar", command=self.withdraw).pack(side=tk.RIGHT, padx=4)
        
        # Inicialmente oculta
        self.withdraw()
        
        # Protocolo de cierre - solo ocultar, no destruir
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
    
    def log_mensaje(self, msg: str):
        """Agregar mensaje al log de auditoría"""
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")
    
    def limpiar_log(self):
        """Limpiar el contenido del log"""
        self.txt_log.configure(state="normal")
        self.txt_log.delete(1.0, tk.END)
        self.txt_log.configure(state="disabled")
    
    def mostrar(self):
        """Mostrar la ventana de auditoría"""
        self.deiconify()
        self.lift()

# ===============================
# Modelo de Procesos y Estados
# ===============================


# Tiempo

def generar_duracion_ejecucion_variada() -> int:
    """
    Genera duración de ejecución variada y observable:
    - 30% procesos cortos (3-5 ticks = 9-15 segundos)
    - 40% procesos normales (6-10 ticks = 18-30 segundos)  
    - 25% procesos largos (12-18 ticks = 36-54 segundos)
    - 5% procesos muy largos (20-30 ticks = 60-90 segundos)
    """
    tipo = random.random()
    if tipo < 0.3:  # Procesos cortos
        return random.randint(3, 5)
    elif tipo < 0.7:  # Procesos normales
        return random.randint(6, 10)
    elif tipo < 0.95:  # Procesos largos
        return random.randint(12, 18)
    else:  # Procesos muy largos
        return random.randint(20, 30)

def generar_tiempo_ejecucion_variado() -> int:
    """Genera tiempo variado para Listo -> Ejecución (4, 7, o 9 ticks)"""
    opciones = [4, 7, 9]
    return random.choice(opciones)

def generar_tiempo_bloqueo() -> int:
    """Genera tiempo de bloqueo (3-5 ticks)"""
    return random.randint(3, 5)

def generar_tiempo_admision_variado() -> int:
    """Genera tiempo de admisión FIJO para Nuevo -> Listo (siempre 3 ticks)"""
    return 3

def generar_tiempo_espera_cpu() -> int:
    """Genera tiempo de espera variado en Listo antes de poder ejecutar (4, 7, o 9 ticks)"""
    return generar_tiempo_ejecucion_variado()

def generar_linger_zombi_variado() -> int:
    """Genera tiempo de linger para zombis (5-12 ticks = 15-36 segundos)"""
    return random.randint(5, 12)

# ===============================
# Modelo de Proceso y Planificador
# ===============================

ESTADOS = (
    "Listo",
    "Ejecución", 
    "Bloqueado",
    "Zombi",
    "Finalizado",
)

ESTADO_COLOR = {
    "Nuevo": "#D0E1FF",        # azul claro
    "Listo": "#E7FFD0",        # verde claro
    "Ejecución": "#FFF3B0",    # amarillo claro
    "Bloqueado": "#FFB3B3",    # rojo claro
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
    tiempo_admision: int = 0         # ticks requeridos para pasar de Nuevo a Listo
    tiempo_espera_cpu: int = 0       # ticks que debe esperar en Listo antes de poder ejecutar
    tiempo_bloqueo: int = 0          # ticks que permanecerá en Bloqueado (3-5 ticks)
    proceso_dependencia: Optional[int] = None  # PID del proceso del cual depende cuando está bloqueado
    linger_zombi: int = 0            # ticks que permanecerá en Zombi
    tiempo_finalizado: float = 0     # timestamp cuando pasó a Finalizado (para auto-eliminación)
    padre: Optional[int] = None
    automatizado: bool = True
    # Recursos del sistema
    cpu_percent: float = 0.0         # Porcentaje de CPU (0-100%)
    memoria_mb: float = 0.0          # Memoria en MB
    disco_percent: float = 0.0       # Porcentaje de disco (0-100%)

    def to_row(self) -> List[str]:
        duracion_str = f"{self.duracion_ejecucion}" if self.duracion_ejecucion > 0 else "Auto"
        
        # Mostrar dependencia en el nombre si está bloqueado
        nombre_display = self.nombre
        if self.estado == "Bloqueado" and self.proceso_dependencia:
            nombre_display = f"{self.nombre} (→{self.proceso_dependencia})"
        
        return [
            str(self.pid),
            nombre_display,
            self.estado,
            str(self.tiempo_estado),
            duracion_str,
            f"{self.cpu_percent:.1f}%",
            f"{self.memoria_mb:.0f} MB",
            f"{self.disco_percent:.1f}%",
        ]

class Planificador:
    def __init__(self):
        self.cola_listos: List[int] = []  # pids
        self.procesos_bloqueados: List[int] = []  # pids de procesos bloqueados
        self.en_ejecucion: Optional[int] = None
        self.proceso_con_prioridad: Optional[int] = None  # PID del proceso ejecutándose por aging

    def admitir(self, proceso: Proceso):
        if proceso.estado == "Nuevo":
            proceso.estado = "Listo"
            proceso.tiempo_estado = 0
            self.cola_listos.append(proceso.pid)

    def asignar_cpu(self, procesos: Dict[int, Proceso]):
        # FIFO estricto: el primero en la cola es el próximo en ejecutar
        if self.en_ejecucion is None and self.cola_listos:
            # Tomar siempre el primer proceso de la cola (FIFO)
            pid = self.cola_listos[0]
            p = procesos.get(pid)
            if p and p.estado == "Listo":
                # Verificar si ha esperado el tiempo mínimo
                if p.tiempo_estado >= p.tiempo_espera_cpu:
                    # Ha esperado suficiente, puede ejecutar
                    self.cola_listos.pop(0)
                    p.estado = "Ejecución"
                    p.tiempo_estado = 0
                    if p.duracion_ejecucion <= 0:
                        p.duracion_ejecucion = generar_duracion_ejecucion_variada()
                    self.en_ejecucion = pid
    
    def bloquear_proceso(self, proceso: Proceso, procesos_disponibles: Dict[int, Proceso]):
        """Bloquea un proceso que está en ejecución y establece dependencia"""
        if proceso.estado == "Ejecución":
            proceso.estado = "Bloqueado"
            proceso.tiempo_estado = 0
            proceso.tiempo_bloqueo = generar_tiempo_bloqueo()
            
            # Buscar un proceso del cual depender (solo Listo o Ejecución)
            candidatos_dependencia = [
                p for p in procesos_disponibles.values() 
                if p.pid != proceso.pid and p.estado in ["Listo", "Ejecución"]
            ]
            
            if candidatos_dependencia:
                # Elegir el proceso con menor PID (más antiguo) como dependencia
                proceso_dependencia = min(candidatos_dependencia, key=lambda x: x.pid)
                proceso.proceso_dependencia = proceso_dependencia.pid
            else:
                proceso.proceso_dependencia = None
                
            self.procesos_bloqueados.append(proceso.pid)
            self.en_ejecucion = None
    
    def desbloquear_proceso(self, proceso: Proceso):
        """Desbloquea un proceso y lo devuelve a Listo"""
        if proceso.estado == "Bloqueado" and proceso.pid in self.procesos_bloqueados:
            proceso.estado = "Listo"
            proceso.tiempo_estado = 0
            proceso.proceso_dependencia = None  # Limpiar dependencia
            self.procesos_bloqueados.remove(proceso.pid)
            self.cola_listos.append(proceso.pid)  # Va al final de la cola FIFO

    def tick(self, procesos: Dict[int, Proceso]):
        # En el modo automático solo aseguramos que haya asignación si está libre
        if self.en_ejecucion is None:
            self.asignar_cpu(procesos)

# ===============================
# Interfaz de Usuario Tkinter
# ===============================

def generar_duracion_ejecucion_variada() -> int:
    """
    Genera duración de ejecución variada automáticamente (más lenta para observar):
    - 30% procesos cortos (3-5 ticks)
    - 40% procesos normales (6-10 ticks)  
    - 25% procesos largos (12-18 ticks)
    - 5% procesos muy largos (20-30 ticks)
    """
    tipo = random.random()
    if tipo < 0.3:  # Procesos cortos
        return random.randint(3, 5)
    elif tipo < 0.7:  # Procesos normales
        return random.randint(6, 10)
    elif tipo < 0.95:  # Procesos largos
        return random.randint(12, 18)
    else:  # Procesos muy largos
        return random.randint(20, 30)

# FUNCIÓN ELIMINADA: estaba duplicada y causaba el error de tiempos

def generar_linger_zombi_variado() -> int:
    """Genera tiempo de linger para zombis (más lento)"""
    return random.randint(5, 12)

class TaskManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mini Administrador de Tareas - SO")
        self.geometry("1000x600")
        self.minsize(900, 550)

        # Modelo
        self.procesos: Dict[int, Proceso] = {}
        self.planificador = Planificador()

        # Configuración de reloj automático
        self.tick_ms = 1500  # ms por tick (1.5 segundos - más rápido para mejor dinamismo)
        self.cpu_corriendo = False  # NO iniciar automáticamente - esperar comando del usuario

        # Sistema completamente automático (sin opciones de configuración)
        self.auto_progress = tk.BooleanVar(value=True)  # Siempre activo
        
        # Lista de PIDs especiales que se convertirán en zombis automáticamente
        self.pids_especiales = []  # Guardaremos 3 PIDs aleatorios aquí
        self.finalizados_pendientes_zombi = {}  # PID -> tiempo_finalizacion para conversión a zombi

        # Contador persistente de procesos finalizados (no se reinicia al eliminar)
        self.total_finalizados_historico = 0

        # Límites de recursos del sistema
        self.cpu_total_disponible = 100.0      # 100% CPU total
        self.memoria_total_disponible = 8192.0  # 8 GB de RAM total
        self.disco_total_disponible = 100.0    # 100% disco total

        # Variables para creación automática de procesos
        self.auto_process_counter = 0
        self.max_auto_processes = 3
        self.auto_process_timer = 0
        self.auto_process_interval = random.randint(5, 6)  # 5-6 ticks
        self.procesos_automaticos = set()  # PIDs de procesos creados automáticamente

        # Construcción UI
        self._build_ui()
        
        # Crear ventana de auditoría
        self.ventana_auditoria = VentanaAuditoria(self)
        
        self._log("Simulador de Sistema Operativo iniciado automáticamente.")

        # Inicio automático del sistema
        self.after(200, self._refrescar_ui)
        self.after(1000, self._start_cpu)  # Iniciar CPU automáticamente tras 1 segundo

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

        columns = ("PID", "Nombre", "Estado", "Tiempo", "Duración", "CPU", "Memoria", "Disco")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=18)
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Duración":
                self.tree.heading(col, text="Duración Ejec.")
            elif col == "CPU":
                self.tree.heading(col, text="CPU")
            elif col == "Memoria":
                self.tree.heading(col, text="Memoria")
            elif col == "Disco":
                self.tree.heading(col, text="Disco")
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
        
        # Recursos del sistema
        self.lbl_recursos = ttk.Label(left, text="Recursos del Sistema: CPU: 0% | RAM: 0 MB/8192 MB | Disco: 0%", 
                                     foreground="blue")
        self.lbl_recursos.grid(row=3, column=0, columnspan=2, sticky="w", pady=(2, 0))

        # Panel derecho - Controles
        right = ttk.Frame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        right.columnconfigure(0, weight=1)

        # Sección CPU y flujo (simplificado para SO automático)
        grp_cpu = ttk.LabelFrame(right, text="CPU / Flujo automático")
        grp_cpu.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.btn_start = ttk.Button(grp_cpu, text="▶ Iniciar Simulación", command=self._start_cpu)
        self.btn_stop = ttk.Button(grp_cpu, text="⏸ Pausar Simulación", command=self._stop_cpu)
        self.btn_start.grid(row=0, column=0, padx=4, pady=4)
        self.btn_stop.grid(row=0, column=1, padx=4, pady=4)
        
        # Inicialmente pausado: botón Iniciar habilitado, Pausar deshabilitado
        self._actualizar_botones_control()

        ttk.Checkbutton(grp_cpu, text="Progreso automático", variable=self.auto_progress).grid(row=1, column=0, columnspan=2, padx=4, pady=4, sticky="w")

        # Sección creación
        grp_crea = ttk.LabelFrame(right, text="Procesos")
        grp_crea.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(grp_crea, text="Nombre").grid(row=0, column=0, padx=4, pady=4, sticky="e")
        self.ent_nombre = ttk.Entry(grp_crea)
        self.ent_nombre.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.ent_nombre.insert(0, "Tarea")

        btn_crear = ttk.Button(grp_crea, text="Crear Proceso", command=self._crear_proceso)
        btn_crear.grid(row=1, column=0, padx=4, pady=4)
        btn_crear5 = ttk.Button(grp_crea, text="Crear 5", command=lambda: self._crear_varios(5))
        btn_crear5.grid(row=1, column=1, padx=4, pady=4)

        # Acciones manuales
        grp_acc = ttk.LabelFrame(right, text="Acciones manuales")
        grp_acc.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(grp_acc, text="Kill Tarea", command=self._finalizar_sel).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(grp_acc, text="Kill Zombi", command=self._kill_zombi).grid(row=0, column=1, padx=4, pady=4)

        # Leyenda de colores de estados
        grp_leg = ttk.LabelFrame(right, text="Leyenda de estados")
        grp_leg.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        r = 0
        c = 0
        for estado, color in ESTADO_COLOR.items():
            swatch = tk.Canvas(grp_leg, width=12, height=12, highlightthickness=1, highlightbackground="#888")
            swatch.create_rectangle(0, 0, 12, 12, fill=color, outline="")
            swatch.grid(row=r, column=c*2, padx=(4, 2), pady=2, sticky="w")
            ttk.Label(grp_leg, text=estado, font=("Segoe UI", 8)).grid(row=r, column=c*2+1, padx=(2, 8), pady=2, sticky="w")
            c += 1
            if c >= 2:  # Solo 2 columnas en lugar de 3
                c = 0
                r += 1

        # Auditoría
        grp_auditoria = ttk.LabelFrame(right, text="Auditoría")
        grp_auditoria.grid(row=4, column=0, sticky="ew")
        
        btn_auditoria = ttk.Button(grp_auditoria, text="📋 Abrir Log de Eventos", command=self._abrir_auditoria)
        btn_auditoria.pack(padx=8, pady=8)

    # ---------- Utilidades ----------
    def _abrir_auditoria(self):
        """Abrir la ventana de auditoría"""
        self.ventana_auditoria.mostrar()
    
    def _log(self, msg: str):
        """Registrar mensaje en la ventana de auditoría"""
        self.ventana_auditoria.log_mensaje(msg)

    def _selected_pids(self) -> List[int]:
        sel = []
        for iid in self.tree.selection():
            try:
                pid = int(self.tree.set(iid, "PID"))
                sel.append(pid)
            except Exception:
                continue
        return sel

    def _actualizar_pids_especiales(self):
        """Actualiza la lista de PIDs especiales dinámicamente: 1 por cada grupo de 9 procesos (menos zombis)"""
        total_procesos = len(self.procesos)
        # Calcular cuántos PIDs especiales necesitamos: 1 por cada 9 procesos (redondeando hacia arriba)
        zombis_objetivo = (total_procesos + 8) // 9  # Equivale a math.ceil(total_procesos / 9)
        
        self._log(f"📊 ACTUALIZACIÓN PIDs: Total={total_procesos}, Objetivo zombis={zombis_objetivo} (cada 9), Actuales={len(self.pids_especiales)} {self.pids_especiales}")
        
        # Si necesitamos más PIDs especiales (se agregaron procesos)
        if len(self.pids_especiales) < zombis_objetivo:
            # Obtener PIDs candidatos (que no sean especiales aún)
            candidatos = [pid for pid in self.procesos.keys() if pid not in self.pids_especiales]
            self._log(f"📊 Necesitamos {zombis_objetivo - len(self.pids_especiales)} PIDs más. Candidatos: {candidatos}")
            
            # Agregar PIDs aleatorios hasta alcanzar el objetivo
            while len(self.pids_especiales) < zombis_objetivo and candidatos:
                nuevo_especial = random.choice(candidatos)
                self.pids_especiales.append(nuevo_especial)
                candidatos.remove(nuevo_especial)
                
                # Calcular en qué "grupo de 9" estamos
                grupo_actual = (len(self.pids_especiales) - 1) * 9 + 1
                grupo_hasta = len(self.pids_especiales) * 9
                self._log(f"🎯 PID {nuevo_especial} seleccionado para zombi #{len(self.pids_especiales)} (procesos {grupo_actual}-{grupo_hasta})")
        
        # Si tenemos demasiados PIDs especiales (por eliminación de procesos)
        elif len(self.pids_especiales) > zombis_objetivo:
            # Remover PIDs que ya no existen en el sistema
            pids_especiales_antiguos = self.pids_especiales.copy()
            self.pids_especiales = [pid for pid in self.pids_especiales if pid in self.procesos]
            
            if len(pids_especiales_antiguos) != len(self.pids_especiales):
                self._log(f"🎯 PIDs especiales limpiados (procesos eliminados del sistema)")
            
            # Si aún tenemos demasiados, remover algunos aleatoriamente
            while len(self.pids_especiales) > zombis_objetivo:
                pid_a_remover = random.choice(self.pids_especiales)
                self.pids_especiales.remove(pid_a_remover)
                self._log(f"🎯 PID {pid_a_remover} removido de especiales (reducción de procesos)")
        
        self._log(f"📊 PIDs especiales FINAL: {self.pids_especiales} ({len(self.pids_especiales)} zombis para {total_procesos} procesos)")

    def _finalizar_proceso(self, proceso: Proceso, razon: str = ""):
        """Marca un proceso como finalizado y registra el timestamp"""
        proceso.estado = "Finalizado"
        proceso.tiempo_estado = 0
        proceso.tiempo_finalizado = time.time()
        
        # Incrementar contador persistente de finalizados
        self.total_finalizados_historico += 1
        
        # Si es un PID especial, marcarlo para conversión automática a zombi en 4 segundos
        if proceso.pid in self.pids_especiales:
            self.finalizados_pendientes_zombi[proceso.pid] = time.time()
            self._log(f"⭐ PID {proceso.pid} es ESPECIAL - programado para zombi en 4 segundos")
        else:
            self._log(f"📋 PID {proceso.pid} es NORMAL - será eliminado en 3 ticks")
        
        msg = f"PID {proceso.pid} finalizado"
        if razon:
            msg += f" ({razon})"
        self._log(msg + ".")
        
        # Debug: mostrar estado de PIDs especiales
        self._log(f"📊 PIDs especiales actuales: {self.pids_especiales}")
        self._log(f"📊 Pendientes para zombi: {list(self.finalizados_pendientes_zombi.keys())}")

    def _distribuir_recursos_sistema(self):
        """Distribuye recursos aleatoriamente entre procesos pero respetando límites del sistema"""
        # Primero, asignar recursos base según estado
        for proceso in self.procesos.values():
            if proceso.estado == "Nuevo":
                proceso.cpu_percent = 0.0
                proceso.memoria_mb = 5.0  # Estructuras base
                proceso.disco_percent = 0.0
                
            elif proceso.estado == "Listo":
                proceso.cpu_percent = 0.0  # No ejecuta aún
                proceso.memoria_mb = random.uniform(10.0, 50.0)  # Memoria reservada
                proceso.disco_percent = 0.0
                
            elif proceso.estado == "Ejecución":
                # ASIGNAR CPU DIRECTAMENTE AQUÍ
                cpu_asignada = random.uniform(15.0, 45.0)
                proceso.cpu_percent = cpu_asignada
                proceso.memoria_mb = random.uniform(50.0, 200.0)  # Memoria para ejecución
                # Disco (40% probabilidad de usar)
                if random.random() < 0.4:
                    proceso.disco_percent = random.uniform(5.0, 25.0)
                else:
                    proceso.disco_percent = 0.0
                
            elif proceso.estado == "Bloqueado":
                proceso.cpu_percent = 0.0  # No ejecuta
                # Mantiene la memoria que tenía (no la cambio aquí)
                if proceso.memoria_mb == 0:  # Si es la primera vez
                    proceso.memoria_mb = random.uniform(30.0, 100.0)
                proceso.disco_percent = 0.0  # Esperando evento externo
                
            elif proceso.estado == "Finalizado":
                proceso.cpu_percent = 0.0
                proceso.memoria_mb = 0.0  # Se libera
                proceso.disco_percent = 0.0
                
            elif proceso.estado == "Zombi":
                proceso.cpu_percent = 0.0  # NUNCA consume CPU
                proceso.memoria_mb = 1.0   # Solo entrada en tabla de procesos
                proceso.disco_percent = 0.0
        
        # Normalizar CPU para que no exceda 100% total
        procesos_ejecutando = [p for p in self.procesos.values() if p.estado == "Ejecución"]
        if procesos_ejecutando:
            cpu_total = sum(p.cpu_percent for p in procesos_ejecutando)
            if cpu_total > 100.0:
                factor_cpu = 100.0 / cpu_total
                for proceso in procesos_ejecutando:
                    proceso.cpu_percent *= factor_cpu
            
            # Normalizar disco si excede 100%
            disco_total = sum(p.disco_percent for p in procesos_ejecutando if p.disco_percent > 0)
            if disco_total > 100.0:
                factor_disco = 100.0 / disco_total
                for proceso in procesos_ejecutando:
                    if proceso.disco_percent > 0:
                        proceso.disco_percent *= factor_disco
        
        # Verificar límite de memoria total
        memoria_total = sum(p.memoria_mb for p in self.procesos.values())
        if memoria_total > self.memoria_total_disponible:
            # Escalar proporcionalmente
            factor = self.memoria_total_disponible / memoria_total
            for proceso in self.procesos.values():
                if proceso.memoria_mb > 0:
                    proceso.memoria_mb *= factor

    # ---------- Acciones ----------
    def _crear_proceso(self, nombre: Optional[str] = None, automatizado: Optional[bool] = None):
        # Si se proporciona un nombre específico (como "System"), usarlo
        # Si no, usar el nombre del campo de entrada para procesos manuales
        if nombre is None:
            # Proceso manual desde el botón - usar el campo de texto
            nombre = self.ent_nombre.get() or "Tarea"
        # Todos los procesos son automáticos por defecto
        automatizado = True
        pid = next_pid()
        p = Proceso(
            pid=pid,
            nombre=f"{nombre}-{pid}",
            automatizado=automatizado,
        )
        
        # Asignar tiempos automáticamente para simular SO real
        p.duracion_ejecucion = generar_tiempo_ejecucion_variado()  # 4, 7, 9 ticks para ejecución
        p.tiempo_admision = generar_tiempo_admision_variado()      # Siempre 3 ticks
        p.tiempo_espera_cpu = generar_tiempo_espera_cpu()          # 4, 7, 9 ticks para espera CPU
        p.tiempo_bloqueo = generar_tiempo_bloqueo()                # 3-5 ticks para bloqueo
        
        # Inicializar recursos básicos según estado inicial
        if p.estado == "Nuevo":
            p.cpu_percent = 0.0
            p.memoria_mb = 5.0
            p.disco_percent = 0.0
        
        self.procesos[pid] = p
        
        # Actualizar PIDs especiales según la proporción 1:6
        self._actualizar_pids_especiales()
        
        self._log(f"Creado proceso {p.nombre} (PID={pid}, Nuevo→Listo: {p.tiempo_admision}t, Listo→Ejec: {p.tiempo_espera_cpu}t, Duración: {p.duracion_ejecucion}t). Estado: Nuevo.")

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
        
        # FIFO ESTRICTO: Solo permitir ejecutar si es el primero en la cola de Listo
        if p.estado == "Listo":
            if not self.planificador.cola_listos or self.planificador.cola_listos[0] != pid:
                self._log(f"ERROR FIFO: El proceso {pid} no es el primero en la cola de Listo")
                return
        elif p.estado == "Nuevo":
            # Si está en Nuevo, primero admitirlo a Listo
            self.planificador.admitir(p)
            self._log(f"Proceso {pid} admitido a Listo desde Nuevo")
            return
        else:
            self._log(f"ERROR: El proceso {pid} no puede ejecutar desde estado {p.estado}")
            return
        
        # Preempt actual si hay uno ejecutando
        if self.planificador.en_ejecucion is not None and self.planificador.en_ejecucion != pid:
            actual = self.procesos.get(self.planificador.en_ejecucion)
            if actual and actual.estado == "Ejecución":
                actual.estado = "Listo"
                actual.tiempo_estado = 0
                self.planificador.cola_listos.insert(0, actual.pid)
        
        # Quitar de cola listos y ejecutar (solo si es el primero)
        self.planificador.cola_listos.pop(0)  # Quitar el primer elemento
        p.estado = "Ejecución"
        p.tiempo_estado = 0
        if p.duracion_ejecucion <= 0:
            p.duracion_ejecucion = generar_duracion_ejecucion_variada()
        self.planificador.en_ejecucion = p.pid
        self._log(f"Proceso {pid} ejecutando (FIFO respetado)")
        self._log(f"Forzado a Ejecución: PID {p.pid}.")
        self._refrescar_tree()

    def _finalizar_sel(self):
        for pid in self._selected_pids():
            p = self.procesos.get(pid)
            if not p:
                continue
            if self.planificador.en_ejecucion == pid:
                self.planificador.en_ejecucion = None
            self._finalizar_proceso(p, "manualmente")
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
            p.linger_zombi = generar_linger_zombi_variado()
            self._log(f"PID {pid} enviado a Zombi (linger={p.linger_zombi}).")
        self._refrescar_tree()

    def _recolectar_zombis(self):
        reco = 0
        for p in self.procesos.values():
            if p.estado == "Zombi":
                self._finalizar_proceso(p, "recolección manual de zombi")
                reco += 1
        if reco:
            self._log(f"Recolectados {reco} zombi(s) manualmente.")
        self._refrescar_tree()

    def _kill_zombi(self):
        """Kill solo UN zombi a la vez (el más antiguo por PID)"""
        zombis = [p for p in self.procesos.values() if p.estado == "Zombi"]
        
        if not zombis:
            self._log("No hay zombis para eliminar.")
            return
        
        # Eliminar el zombi más antiguo (menor PID)
        zombi_mas_antiguo = min(zombis, key=lambda x: x.pid)
        pid_eliminado = zombi_mas_antiguo.pid
        
        # Verificar si era un proceso automático antes de eliminarlo
        era_automatico = pid_eliminado in self.procesos_automaticos
        
        del self.procesos[pid_eliminado]
        
        # Si era automático, decrementar contador y remover de la lista
        if era_automatico:
            self.procesos_automaticos.remove(pid_eliminado)
            self.auto_process_counter -= 1
            self._log(f"🤖 Proceso automático PID {pid_eliminado} eliminado. Contador: {self.auto_process_counter}/{self.max_auto_processes}")
        
        # Remover de PIDs especiales si estaba ahí
        if pid_eliminado in self.pids_especiales:
            self.pids_especiales.remove(pid_eliminado)
        
        # Actualizar proporción de PIDs especiales
        self._actualizar_pids_especiales()
        
        self._log(f"💀 KILL: Zombi PID {pid_eliminado} eliminado definitivamente del sistema.")
        self._refrescar_tree()

    def _actualizar_botones_control(self):
        """Actualiza el estado de los botones según si la simulación está corriendo"""
        if self.cpu_corriendo:
            # Simulación corriendo: deshabilitar Iniciar, habilitar Pausar
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")
        else:
            # Simulación pausada: habilitar Iniciar, deshabilitar Pausar
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")

    def _start_cpu(self):
        if not self.cpu_corriendo:
            self.cpu_corriendo = True
            self._actualizar_botones_control()
            self._log("🚀 Simulación iniciada - El tiempo comenzó a correr")
            self._tick_loop()

    def _stop_cpu(self):
        self.cpu_corriendo = False
        self._actualizar_botones_control()
        self._log("⏸ Simulación pausada - El tiempo se detuvo")

    # ---------- Bucle principal de ticks ----------
    def _tick_loop(self):
        if not self.cpu_corriendo:
            return

        # 0) Verificar que tengamos PIDs especiales según proporción dinámica
        if self.procesos:
            total_procesos = len(self.procesos)
            zombis_objetivo = (total_procesos + 8) // 9  # 1 por cada grupo de 9
            if len(self.pids_especiales) < zombis_objetivo:
                self._log(f"⚠️ Faltan PIDs especiales ({len(self.pids_especiales)}/{zombis_objetivo}), actualizando...")
                self._actualizar_pids_especiales()

        # 0.1) Creación automática de procesos cada 5-6 ticks (máximo 3)
        self.auto_process_timer += 1
        if (self.auto_process_counter < self.max_auto_processes and 
            self.auto_process_timer >= self.auto_process_interval):
            # Crear proceso automático con nombre "System"
            pid_anterior = max(self.procesos.keys()) if self.procesos else 0
            self._crear_proceso(nombre="System")
            # Encontrar el nuevo PID creado y agregarlo a la lista de automáticos
            nuevo_pid = max(self.procesos.keys())
            if nuevo_pid != pid_anterior:
                self.procesos_automaticos.add(nuevo_pid)
            
            self.auto_process_counter += 1
            self.auto_process_timer = 0
            self.auto_process_interval = random.randint(5, 6)  # Nuevo intervalo aleatorio
            self._log(f"🤖 Proceso automático creado ({self.auto_process_counter}/{self.max_auto_processes}) - PID {nuevo_pid}")

        # 1) Cambios automáticos de estado
        if self.auto_progress.get():
            # Nuevo -> Listo ESTRICTAMENTE SECUENCIAL (tiempo variable: 4, 5, 7 ticks)
            procesos_nuevos = [p for p in self.procesos.values() if p.estado == "Nuevo"]
            
            # Incrementar tiempo solo del proceso con menor PID en Nuevo
            if procesos_nuevos:
                proceso_siguiente = min(procesos_nuevos, key=lambda x: x.pid)
                proceso_siguiente.tiempo_estado += 1
                
                # Cambiar a Listo cuando alcance su tiempo de admisión
                if proceso_siguiente.tiempo_estado >= proceso_siguiente.tiempo_admision:
                    self.planificador.admitir(proceso_siguiente)
                    self._log(f"PID {proceso_siguiente.pid}: Nuevo → Listo ({proceso_siguiente.tiempo_admision} ticks)")

            # Listo -> Ejecución: solo el primero en cola (tiempo variable)
            for p in self.procesos.values():
                if p.estado == "Listo":
                    p.tiempo_estado += 1

            # Asignar CPU con PRIORIDAD POR ANTIGÜEDAD (aging anti-starvation)
            if self.planificador.en_ejecucion is None and self.planificador.cola_listos:
                
                # 1. Buscar procesos con MUCHO tiempo esperando (20+ ticks) - PRIORIDAD
                procesos_hambrientos = []
                for pid in self.planificador.cola_listos:
                    p = self.procesos.get(pid)
                    if p and p.estado == "Listo" and p.tiempo_estado >= 20:
                        procesos_hambrientos.append(p)
                
                # 2. Si hay procesos hambrientos, dar prioridad al más antiguo
                if procesos_hambrientos:
                    proceso_elegido = min(procesos_hambrientos, key=lambda x: x.pid)  # Más antiguo por PID
                    # Mover al frente de la cola para darle prioridad inmediata
                    self.planificador.cola_listos.remove(proceso_elegido.pid)
                    self.planificador.cola_listos.insert(0, proceso_elegido.pid)
                    self._log(f"🚨 AGING: PID {proceso_elegido.pid} promovido por hambruna ({proceso_elegido.tiempo_estado} ticks esperando)")
                
                # 3. Ejecutar el primer proceso de la cola (FIFO normal o proceso promovido)
                pid_primero = self.planificador.cola_listos[0]
                p_primero = self.procesos.get(pid_primero)
                if p_primero and p_primero.estado == "Listo" and p_primero.tiempo_estado >= p_primero.tiempo_espera_cpu:
                    # Ha esperado suficiente, puede ejecutar
                    self.planificador.cola_listos.pop(0)
                    p_primero.estado = "Ejecución"
                    p_primero.tiempo_estado = 0
                    if p_primero.duracion_ejecucion <= 0:
                        p_primero.duracion_ejecucion = generar_duracion_ejecucion_variada()
                    self.planificador.en_ejecucion = p_primero.pid
                    
                    # Marcar si fue por aging y registrar
                    es_por_aging = p_primero.pid in [p.pid for p in procesos_hambrientos]
                    if es_por_aging:
                        self.planificador.proceso_con_prioridad = p_primero.pid
                    
                    tipo_asignacion = "AGING" if es_por_aging else "FIFO"
                    self._log(f"PID {p_primero.pid}: Listo → Ejecución ({tipo_asignacion}, esperó {p_primero.tiempo_estado + p_primero.tiempo_espera_cpu} ticks total)")

            # Ejecución -> Bloqueado/Zombi/Finalizado (tiempo variable)
            pid = self.planificador.en_ejecucion
            if pid is not None:
                p = self.procesos.get(pid)
                if p and p.estado == "Ejecución":
                    p.tiempo_estado += 1
                    
                    # Calcular probabilidad de bloqueo basada en la CARGA del sistema
                    procesos_esperando = len(self.planificador.cola_listos)
                    ya_hay_bloqueados = len(self.planificador.procesos_bloqueados) > 0
                    
                    # Probabilidad aumenta con más procesos esperando (simulando contención de recursos)
                    probabilidad_base = 0.02  # 2% base
                    factor_carga = min(procesos_esperando * 0.015, 0.08)  # Máximo 8% adicional
                    probabilidad_bloqueo = probabilidad_base + factor_carga
                    
                    # Condiciones para bloqueo:
                    # 1. Debe haber procesos esperando
                    # 2. NO debe haber otros procesos ya bloqueados
                    # 3. Debe haber ejecutado al menos 3 ticks
                    # 4. Probabilidad variable según carga del sistema
                    puede_bloquear = (procesos_esperando > 0 and 
                                    not ya_hay_bloqueados and 
                                    p.tiempo_estado >= 3 and 
                                    random.random() < probabilidad_bloqueo)
                    
                    if puede_bloquear:
                        # Si este proceso tenía prioridad, limpiar la marca antes de bloquearlo
                        if self.planificador.proceso_con_prioridad == p.pid:
                            self.planificador.proceso_con_prioridad = None
                            self._log(f"🔓 PRIORIDAD LIBERADA: PID {p.pid} se bloqueó, procesos bloqueados pueden cambiar de estado")
                        
                        # Bloquear el proceso con dependencias
                        self.planificador.bloquear_proceso(p, self.procesos)
                        
                        # Log con información de dependencia
                        if p.proceso_dependencia:
                            proceso_dep = self.procesos.get(p.proceso_dependencia)
                            estado_dep = proceso_dep.estado if proceso_dep else "DESCONOCIDO"
                            self._log(f"PID {p.pid}: Ejecución → Bloqueado (I/O, depende de PID {p.proceso_dependencia} [{estado_dep}])")
                        else:
                            self._log(f"PID {p.pid}: Ejecución → Bloqueado (I/O independiente, prob={probabilidad_bloqueo:.1%})")
                    elif p.tiempo_estado >= p.duracion_ejecucion:
                        # Terminar normalmente
                        self.planificador.en_ejecucion = None
                        
                        # Si este proceso terminó y tenía prioridad, limpiar la marca
                        if self.planificador.proceso_con_prioridad == p.pid:
                            self.planificador.proceso_con_prioridad = None
                            self._log(f"🔓 PRIORIDAD LIBERADA: PID {p.pid} terminó, procesos bloqueados pueden cambiar de estado")
                        
                        # TODOS los procesos van primero a Finalizado
                        # Solo los PIDs especiales se convertirán en zombi después de 4 segundos
                        self._finalizar_proceso(p, f"{p.duracion_ejecucion} ticks completados")
            
            # Bloqueado -> Listo (SOLO si no hay proceso con prioridad ejecutándose)
            for p in self.procesos.values():
                if p.estado == "Bloqueado":
                    p.tiempo_estado += 1
                    if p.tiempo_estado >= p.tiempo_bloqueo:
                        # Verificar condiciones para desbloqueo
                        hay_proceso_prioritario = self.planificador.proceso_con_prioridad is not None
                        
                        # Verificar dependencia del proceso
                        dependencia_resuelta = True
                        if p.proceso_dependencia:
                            proceso_dependencia = self.procesos.get(p.proceso_dependencia)
                            if proceso_dependencia and proceso_dependencia.estado in ["Listo", "Ejecución"]:
                                dependencia_resuelta = False  # Aún depende de un proceso activo
                            else:
                                # La dependencia terminó (Finalizado/Zombi) o no existe, se resuelve
                                dependencia_resuelta = True
                        
                        if not hay_proceso_prioritario and dependencia_resuelta:
                            # No hay prioridad activa y dependencia resuelta, puede desbloquearse
                            self.planificador.desbloquear_proceso(p)
                            if p.proceso_dependencia:
                                self._log(f"PID {p.pid}: Bloqueado → Listo (dependencia PID {p.proceso_dependencia} resuelta)")
                            else:
                                self._log(f"PID {p.pid}: Bloqueado → Listo ({p.tiempo_bloqueo} ticks, sin dependencia)")
                        elif hay_proceso_prioritario:
                            # Hay proceso prioritario, debe esperar
                            pid_prioritario = self.planificador.proceso_con_prioridad
                            self._log(f"⏳ PID {p.pid}: Listo para cambiar, esperando proceso prioritario PID {pid_prioritario}")
                        elif not dependencia_resuelta:
                            # Dependencia aún activa, debe esperar
                            proceso_dep = self.procesos.get(p.proceso_dependencia)
                            estado_dep = proceso_dep.estado if proceso_dep else "INEXISTENTE"
                            self._log(f"🔗 PID {p.pid}: Esperando dependencia PID {p.proceso_dependencia} [{estado_dep}]")

        # 2) Los zombis permanecen para siempre - NO se recolectan automáticamente
        # Solo pueden ser eliminados manualmente con el botón "Kill Zombi"
        for p in self.procesos.values():
            if p.estado == "Zombi":
                p.tiempo_estado += 1  # Solo incrementar contador, no hacer nada más

        # 3) Incrementar tiempo de procesos Finalizados (para auto-eliminación)
        for p in self.procesos.values():
            if p.estado == "Finalizado":
                p.tiempo_estado += 1

        # 4) Revisar PIDs especiales finalizados para conversión automática a zombi (4 segundos)
        tiempo_actual = time.time()
        pids_a_convertir_zombi = []
        
        # Debug: mostrar PIDs pendientes y sus tiempos
        if self.finalizados_pendientes_zombi:
            self._log(f"⏰ Revisando PIDs pendientes para zombi:")
            for pid, tiempo_finalizacion in self.finalizados_pendientes_zombi.items():
                tiempo_transcurrido = tiempo_actual - tiempo_finalizacion
                self._log(f"   PID {pid}: {tiempo_transcurrido:.1f}s transcurridos (necesita 4s)")
        
        for pid, tiempo_finalizacion in list(self.finalizados_pendientes_zombi.items()):
            tiempo_transcurrido = tiempo_actual - tiempo_finalizacion
            if tiempo_transcurrido >= 4:  # 4 segundos
                pids_a_convertir_zombi.append(pid)
                self._log(f"✅ PID {pid} listo para conversión a zombi ({tiempo_transcurrido:.1f}s >= 4s)")
        
        # Convertir PIDs especiales a zombi automáticamente
        for pid in pids_a_convertir_zombi:
            if pid in self.procesos:
                p = self.procesos[pid]
                if p.estado == "Finalizado":
                    p.estado = "Zombi"
                    p.tiempo_estado = 0
                    p.linger_zombi = generar_linger_zombi_variado()
                    self._log(f"PID {pid}: Finalizado → Zombi (conversión automática)")
                del self.finalizados_pendientes_zombi[pid]
        
        # 5) Eliminar procesos finalizados después de 3 ticks (procesos normales) o conversión a zombi (PIDs especiales)
        pids_a_eliminar = []
        for p in self.procesos.values():
            if p.estado == "Finalizado":
                if p.pid not in self.pids_especiales:
                    # Proceso normal: eliminar después de 3 ticks
                    if p.tiempo_estado >= 3:
                        pids_a_eliminar.append(p.pid)
                else:
                    # PID especial: usar tiempo real para conversión a zombi (4 segundos)
                    if p.tiempo_finalizado > 0:
                        tiempo_transcurrido = tiempo_actual - p.tiempo_finalizado
                        if tiempo_transcurrido >= 80:
                            # PID especial encontrado después de 80 segundos - verificar si ya se convirtió
                            self._log(f"🛡️ PID {p.pid} protegido (PID especial en Finalizado, esperando conversión a zombi)")
        
        # Eliminar SOLO los procesos normales (no PIDs especiales)
        for pid in pids_a_eliminar:
            if pid in self.procesos:
                proceso_eliminado = self.procesos[pid]
                
                # Verificar si era un proceso automático antes de eliminarlo
                era_automatico = pid in self.procesos_automaticos
                
                del self.procesos[pid]
                
                # Si era automático, decrementar contador y remover de la lista
                if era_automatico:
                    self.procesos_automaticos.remove(pid)
                    self.auto_process_counter -= 1
                    self._log(f"🤖 Proceso automático PID {pid} eliminado. Contador: {self.auto_process_counter}/{self.max_auto_processes}")
                
                self._log(f"PID {pid} ({proceso_eliminado.nombre}) eliminado automáticamente tras 3 ticks (proceso normal).")
        
        # Actualizar proporción de PIDs especiales después de eliminar procesos
        if pids_a_eliminar:
            self._actualizar_pids_especiales()

        # 5.5) Actualizar y distribuir recursos del sistema respetando límites
        self._distribuir_recursos_sistema()

        # 6) Refrescar vista
        self._refrescar_tree()

        # Programar siguiente tick
        self.after(self.tick_ms, self._tick_loop)

    # ---------- Refresco de Treeview ----------
    def _refrescar_tree(self):
        # Sync items - solo mostrar procesos que no estén en estado "Nuevo"
        existentes = set(self.tree.get_children())
        por_pid = {self.tree.set(i, "PID"): i for i in existentes}

        # Filtrar procesos: mostrar solo desde "Listo" en adelante
        procesos_visibles = [p for p in self.procesos.values() if p.estado != "Nuevo"]

        # actualizar/insertar solo procesos visibles
        for p in procesos_visibles:
            row = p.to_row()
            pid_str = str(p.pid)
            if pid_str in por_pid:
                iid = por_pid[pid_str]
                # Actualizar TODAS las columnas incluyendo CPU, Memoria, Disco
                columnas = ("PID", "Nombre", "Estado", "Tiempo", "Duración", "CPU", "Memoria", "Disco")
                for col, val in zip(columnas, row):
                    self.tree.set(iid, col, val)
                # actualizar tag de color según estado
                self.tree.item(iid, tags=(p.estado,))
            else:
                iid = self.tree.insert("", "end", values=row, tags=(p.estado,))
                por_pid[pid_str] = iid

        # eliminar los que ya no existen o están en estado "Nuevo"
        pids_visibles = {str(p.pid) for p in procesos_visibles}
        for pid_str, iid in list(por_pid.items()):
            if pid_str not in pids_visibles:
                self.tree.delete(iid)
                del por_pid[pid_str]

        # actualizar resumen
        total = len(self.procesos)
        total_visibles = len(procesos_visibles)
        por_estado: Dict[str, int] = {e: 0 for e in ESTADOS}
        for p in self.procesos.values():
            por_estado[p.estado] = por_estado.get(p.estado, 0) + 1
        
        # Mostrar estadísticas con contador persistente para Finalizado
        resumen_partes = []
        for e in ESTADOS:
            if e == "Finalizado":
                # Usar contador persistente para finalizados
                resumen_partes.append(f"{e}: {self.total_finalizados_historico}")
            else:
                resumen_partes.append(f"{e}: {por_estado.get(e, 0)}")
        
        resumen = " | ".join(resumen_partes)
        self.lbl_stats.configure(text=f"Total: {total} procesos | Visibles: {total_visibles} | {resumen}")
        
        # Actualizar recursos totales del sistema
        cpu_total = sum(p.cpu_percent for p in self.procesos.values())
        memoria_total = sum(p.memoria_mb for p in self.procesos.values())
        disco_total = sum(p.disco_percent for p in self.procesos.values())
        
        recursos_text = (f"Recursos del Sistema: CPU: {cpu_total:.1f}% | "
                        f"RAM: {memoria_total:.0f} MB/{self.memoria_total_disponible:.0f} MB | "
                        f"Disco: {disco_total:.1f}%")
        self.lbl_recursos.configure(text=recursos_text)

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
